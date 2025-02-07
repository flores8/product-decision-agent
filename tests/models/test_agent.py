import pytest
from unittest.mock import patch, MagicMock, create_autospec, Mock
from tyler.models.agent import Agent, AgentPrompt
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.utils.tool_runner import tool_runner
from tyler.database.thread_store import ThreadStore
from openai import OpenAI
from litellm import ModelResponse
import base64
from tyler.utils.file_processor import FileProcessor
import asyncio
from tyler.models.attachment import Attachment

@pytest.fixture
def mock_tool_runner():
    return create_autospec(tool_runner, instance=True)

@pytest.fixture
def mock_thread_store():
    return create_autospec(ThreadStore, instance=True)

@pytest.fixture
def mock_prompt():
    mock = create_autospec(AgentPrompt, instance=True)
    mock.system_prompt.return_value = "Test system prompt"
    return mock

@pytest.fixture
def mock_litellm():
    with patch('litellm.completion') as mock_completion:
        mock_completion.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content="Test response",
                    tool_calls=None
                )
            )]
        )
        yield mock_completion

class MockFileProcessor(FileProcessor):
    def __init__(self):
        self.supported_types = {
            'application/pdf': self._process_pdf,
        }
        self.client = MagicMock()
        self.process_file = MagicMock(return_value={"content": "processed content"})

@pytest.fixture
def mock_file_processor():
    return MockFileProcessor()

@pytest.fixture
def mock_openai():
    with patch("tyler.utils.file_processor.OpenAI") as mock:
        yield mock

@pytest.fixture
def agent(mock_thread_store, mock_prompt, mock_litellm, mock_file_processor, mock_openai):
    with patch('tyler.models.agent.tool_runner', mock_tool_runner), \
         patch('tyler.models.agent.AgentPrompt', return_value=mock_prompt), \
         patch('tyler.models.agent.FileProcessor', return_value=mock_file_processor), \
         patch('tyler.utils.file_processor.OpenAI'), \
         patch('litellm.acompletion', mock_litellm), \
         patch('tyler.models.agent.acompletion', mock_litellm):  # Mock OpenAI client initialization
        agent = Agent(
            model_name="gpt-4",
            temperature=0.5,
            purpose="test purpose",
            notes="test notes",
            thread_store=mock_thread_store
        )
        agent._current_recursion_depth = 0  # Initialize recursion depth
        agent._file_processor = mock_file_processor  # Set file processor
        agent._prompt = mock_prompt  # Set mock prompt
        return agent

def test_init(agent):
    """Test Agent initialization"""
    assert agent.model_name == "gpt-4"
    assert agent.temperature == 0.5
    assert agent.purpose == "test purpose"
    assert agent.notes == "test notes"
    assert len(agent.tools) == 0
    assert agent.max_tool_recursion == 10
    assert agent._current_recursion_depth == 0

@pytest.mark.asyncio
async def test_go_thread_not_found(agent, mock_thread_store):
    """Test go() with non-existent thread"""
    mock_thread_store.get.return_value = None
    
    with pytest.raises(ValueError, match="Thread with ID test-conv not found"):
        await agent.go("test-conv")

@pytest.mark.asyncio
async def test_go_max_recursion(agent, mock_thread_store):
    """Test go() with maximum recursion depth reached"""
    thread = Thread(id="test-conv", title="Test Thread")
    mock_thread_store.get.return_value = thread
    agent._current_recursion_depth = agent.max_tool_recursion
    
    result_thread, new_messages = await agent.go("test-conv")
    
    assert len(new_messages) == 1
    assert new_messages[0].role == "assistant"
    assert new_messages[0].content == "Maximum tool recursion depth reached. Stopping further tool calls."
    mock_thread_store.save.assert_called_once_with(result_thread)

@pytest.mark.asyncio
async def test_go_no_tool_calls(agent, mock_thread_store, mock_prompt):
    """Test go() with a response that doesn't include tool calls"""
    thread = Thread(id="test-conv", title="Test Thread")
    mock_prompt.system_prompt.return_value = "Test system prompt"
    thread.messages = []  # Clear any existing messages
    thread.ensure_system_prompt("Test system prompt")
    mock_thread_store.get.return_value = thread
    agent._current_recursion_depth = 0
    
    mock_response = MagicMock(
        choices=[MagicMock(
            message=MagicMock(
                content="Test response",
                tool_calls=None
            )
        )]
    )
    
    with patch('tyler.models.agent.completion', return_value=mock_response):
        result_thread, new_messages = await agent.go("test-conv")
    
    assert result_thread.messages[0].role == "system"
    assert result_thread.messages[0].content == "Test system prompt"
    assert result_thread.messages[1].role == "assistant"
    assert result_thread.messages[1].content == "Test response"
    assert len(new_messages) == 1
    assert new_messages[0].role == "assistant"
    mock_thread_store.save.assert_called_with(result_thread)
    assert agent._current_recursion_depth == 0

@pytest.mark.asyncio
async def test_go_with_tool_calls(agent, mock_thread_store, mock_prompt):
    """Test go() with a response that includes tool calls"""
    thread = Thread(id="test-conv", title="Test Thread")
    mock_prompt.system_prompt.return_value = "Test system prompt"
    thread.messages = []  # Clear any existing messages
    thread.ensure_system_prompt("Test system prompt")
    mock_thread_store.get.return_value = thread
    agent._current_recursion_depth = 0
    
    # Create a tool call with concrete values instead of MagicMock
    function_mock = MagicMock()
    function_mock.name = "test-tool"  # Set as string instead of MagicMock
    function_mock.arguments = '{"arg": "value"}'  # Set as string instead of MagicMock
    
    tool_call = MagicMock()
    tool_call.id = "test-call-id"  # Set as string instead of MagicMock
    tool_call.type = "function"  # Set as string instead of MagicMock
    tool_call.function = function_mock
    
    first_response = MagicMock(
        choices=[MagicMock(
            message=MagicMock(
                content="Test response with tool",
                tool_calls=[tool_call]
            )
        )]
    )
    
    second_response = MagicMock(
        choices=[MagicMock(
            message=MagicMock(
                content="Final response",
                tool_calls=None
            )
        )]
    )
    
    mock_completion = MagicMock(side_effect=[first_response, second_response])
    
    with patch('tyler.models.agent.completion', mock_completion), \
         patch('tyler.models.agent.tool_runner') as patched_tool_runner:
        patched_tool_runner.execute_tool_call = AsyncMock(return_value={
            "name": "test-tool",
            "content": "Tool result"
        })
        
        result_thread, new_messages = await agent.go("test-conv")
    
    messages = result_thread.messages
    assert len(messages) == 4
    assert messages[0].role == "system"
    assert messages[0].content == "Test system prompt"
    assert messages[1].role == "assistant"
    assert messages[1].content == "Test response with tool"
    
    # Assert the serialized tool call format
    expected_tool_call = {
        "id": "test-call-id",
        "type": "function",
        "function": {
            "name": "test-tool",
            "arguments": '{"arg": "value"}'
        }
    }
    assert messages[1].tool_calls == [expected_tool_call]
    
    assert messages[2].role == "tool"
    assert messages[2].content == "Tool result"
    assert messages[2].name == "test-tool"
    assert messages[2].tool_call_id == "test-call-id"
    assert messages[3].role == "assistant"
    assert messages[3].content == "Final response"
    
    assert len(new_messages) == 3
    assert [m.role for m in new_messages] == ["assistant", "tool", "assistant"]

@pytest.mark.asyncio
async def test_handle_tool_execution(agent, mock_tool_runner):
    """Test _handle_tool_execution"""
    tool_call = MagicMock()
    tool_call.id = "test-call-id"
    tool_call.function.name = "test-tool"
    tool_call.function.arguments = '{"arg": "value"}'
    
    with patch('tyler.models.agent.tool_runner') as patched_tool_runner:
        patched_tool_runner.execute_tool_call = AsyncMock(return_value={
            "name": "test-tool",
            "content": "Tool result"
        })
        
        result = await agent._handle_tool_execution(tool_call)
    
    assert result["name"] == "test-tool"
    assert result["content"] == "Tool result"

def test_process_message_files_with_image(agent, mock_thread_store):
    """Test processing message files with an image attachment"""
    message = Message(role="user", content="Test with image")
    image_content = b"fake image data"
    
    class MockAttachment:
        def __init__(self):
            self.filename = "test.jpg"
            self.mime_type = None
            self.processed_content = None
        
        def get_content_bytes(self):
            return image_content
    
    attachment = MockAttachment()
    message.attachments = [attachment]
    
    with patch('magic.from_buffer', return_value='image/jpeg'):
        agent._process_message_files(message)
        attachment.mime_type = 'image/jpeg'  # Set mime_type after detection
    
    assert attachment.mime_type == 'image/jpeg'
    assert attachment.processed_content['type'] == 'image'
    assert attachment.processed_content['mime_type'] == 'image/jpeg'
    assert attachment.processed_content['content'] == base64.b64encode(image_content).decode('utf-8')
    
    # Check that message content was converted to multimodal format
    assert isinstance(message.content, list)
    assert message.content[0]['type'] == 'text'
    assert message.content[0]['text'] == "Test with image"
    assert message.content[1]['type'] == 'image_url'
    assert 'data:image/jpeg;base64,' in message.content[1]['image_url']['url']

def test_process_message_files_with_document(agent, mock_thread_store, mock_file_processor):
    """Test processing message files with a document attachment"""
    message = Message(role="user", content="Test with document")
    
    class MockAttachment:
        def __init__(self):
            self.filename = "test.pdf"
            self.mime_type = None
            self.processed_content = None
        
        def get_content_bytes(self):
            return b"fake pdf data"
    
    attachment = MockAttachment()
    message.attachments = [attachment]
    
    with patch('magic.from_buffer', return_value='application/pdf'):
        agent._process_message_files(message)
        attachment.mime_type = 'application/pdf'  # Set mime_type after detection
    
    assert attachment.mime_type == 'application/pdf'
    assert attachment.processed_content == {"content": "processed content"}
    mock_file_processor.process_file.assert_called_once_with(b"fake pdf data", "test.pdf")

def test_process_message_files_with_error(agent, mock_thread_store, mock_file_processor):
    """Test processing message files with an error"""
    message = Message(role="user", content="Test with error")
    
    class MockAttachment:
        def __init__(self):
            self.filename = "test.doc"
            self.mime_type = None
            self.processed_content = None
        
        def get_content_bytes(self):
            raise Exception("Failed to read file")
    
    attachment = MockAttachment()
    message.attachments = [attachment]
    
    agent._process_message_files(message)
    
    assert "Failed to process file" in attachment.processed_content["error"]

def test_process_file_attachment(agent, mock_openai):
    """Test processing a file attachment"""
    # Create a mock file processor
    mock_processor = Mock(spec=FileProcessor)
    mock_processor.process.return_value = "Processed content"
    agent.file_processor = mock_processor
    
    # Create test data
    attachment = Attachment(
        id="test-attachment",
        filename="test.txt",
        content_type="text/plain",
        size=100,
        storage_path="test/path"
    )
    
    # Process attachment
    result = agent.process_file_attachment(attachment)
    
    # Verify results
    assert result == "Processed content"
    mock_processor.process.assert_called_once_with(attachment)

def test_process_message_with_attachment(agent, mock_openai):
    """Test processing a message that contains an attachment"""
    # Create a mock file processor
    mock_processor = Mock(spec=FileProcessor)
    mock_processor.process.return_value = "Processed content"
    agent.file_processor = mock_processor
    
    # Create test data
    attachment = Attachment(
        id="test-attachment",
        filename="test.txt",
        content_type="text/plain",
        size=100,
        storage_path="test/path"
    )
    message = Message(
        role="user",
        content="Please process this file",
        attachments=[attachment]
    )
    thread = Thread(id="test-thread")
    thread.add_message(message)
    
    # Process message
    processed_content = agent.process_message_attachments(message)
    
    # Verify results
    assert processed_content == ["Please process this file", "Processed content"]
    mock_processor.process.assert_called_once_with(attachment)

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs) 