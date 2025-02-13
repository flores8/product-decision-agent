import pytest
from unittest.mock import patch, MagicMock, create_autospec, Mock, AsyncMock
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
from datetime import datetime, UTC
import os

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
    mock = AsyncMock()
    mock.return_value = ModelResponse(**{
        "id": "test-id",
        "choices": [{
            "finish_reason": "stop",
            "index": 0,
            "message": {
                "content": "Test response",
                "role": "assistant",
                "tool_calls": None
            }
        }],
        "model": "gpt-4",
        "usage": {
            "completion_tokens": 10,
            "prompt_tokens": 20,
            "total_tokens": 30
        }
    })
    
    with patch('litellm.acompletion', mock), \
         patch('tyler.models.agent.acompletion', mock):
        yield mock

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
         patch('tyler.models.agent.acompletion', mock_litellm), \
         patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
        agent = Agent(
            model_name="gpt-4",
            temperature=0.5,
            purpose="test purpose",
            notes="test notes",
            thread_store=mock_thread_store
        )
        agent._iteration_count = 0
        agent._file_processor = mock_file_processor
        agent._prompt = mock_prompt
        return agent

def test_init(agent):
    """Test Agent initialization"""
    assert agent.model_name == "gpt-4"
    assert agent.temperature == 0.5
    assert agent.purpose == "test purpose"
    assert agent.notes == "test notes"
    assert len(agent.tools) == 0
    assert agent.max_tool_iterations == 10
    assert agent._iteration_count == 0

@pytest.mark.asyncio
async def test_go_thread_not_found(agent, mock_thread_store):
    """Test go() with non-existent thread"""
    mock_thread_store.get.return_value = None
    
    with pytest.raises(ValueError, match="Thread with ID test-conv not found"):
        await agent.go("test-conv")

@pytest.mark.asyncio
async def test_go_max_recursion(agent, mock_thread_store):
    """Test go() with maximum iteration count reached"""
    thread = Thread(id="test-conv", title="Test Thread")
    mock_thread_store.get.return_value = thread
    agent._iteration_count = agent.max_tool_iterations
    
    result_thread, new_messages = await agent.go("test-conv")
    
    assert len(new_messages) == 1
    assert new_messages[0].role == "assistant"
    assert new_messages[0].content == "Maximum tool iteration count reached. Stopping further tool calls."
    mock_thread_store.save.assert_called_once_with(result_thread)

@pytest.mark.asyncio
async def test_go_no_tool_calls(agent, mock_thread_store, mock_prompt, mock_litellm):
    """Test go() with a response that doesn't include tool calls"""
    thread = Thread(id="test-conv", title="Test Thread")
    mock_prompt.system_prompt.return_value = "Test system prompt"
    thread.messages = []
    thread.ensure_system_prompt("Test system prompt")
    mock_thread_store.get.return_value = thread
    agent._iteration_count = 0
    
    result_thread, new_messages = await agent.go("test-conv")
    
    assert result_thread.messages[0].role == "system"
    assert result_thread.messages[0].content == "Test system prompt"
    assert result_thread.messages[1].role == "assistant"
    assert result_thread.messages[1].content == "Test response"
    assert len(new_messages) == 1
    assert new_messages[0].role == "assistant"
    assert "metrics" in new_messages[0].model_dump()
    assert "timing" in new_messages[0].metrics
    assert "usage" in new_messages[0].metrics
    mock_thread_store.save.assert_called_with(result_thread)
    assert agent._iteration_count == 0

@pytest.mark.asyncio
async def test_go_with_tool_calls(agent, mock_thread_store, mock_prompt, mock_litellm):
    """Test go() with a response that includes tool calls"""
    thread = Thread(id="test-conv", title="Test Thread")
    mock_prompt.system_prompt.return_value = "Test system prompt"
    thread.messages = []
    thread.ensure_system_prompt("Test system prompt")
    mock_thread_store.get.return_value = thread
    agent._iteration_count = 0
    
    # First response with tool call
    tool_response = ModelResponse(**{
        "id": "test-id",
        "choices": [{
            "finish_reason": "tool_calls",
            "index": 0,
            "message": {
                "content": "Test response with tool",
                "role": "assistant",
                "tool_calls": [{
                    "id": "test-call-id",
                    "type": "function",
                    "function": {
                        "name": "test-tool",
                        "arguments": '{"arg": "value"}'
                    }
                }]
            }
        }],
        "model": "gpt-4",
        "usage": {
            "completion_tokens": 10,
            "prompt_tokens": 20,
            "total_tokens": 30
        }
    })
    
    # Final response without tool calls
    final_response = ModelResponse(**{
        "id": "test-id-2",
        "choices": [{
            "finish_reason": "stop",
            "index": 0,
            "message": {
                "content": "Final response",
                "role": "assistant",
                "tool_calls": None
            }
        }],
        "model": "gpt-4",
        "usage": {
            "completion_tokens": 5,
            "prompt_tokens": 25,
            "total_tokens": 30
        }
    })
    
    mock_litellm.side_effect = [tool_response, final_response]
    
    with patch('tyler.models.agent.tool_runner') as patched_tool_runner:
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
    
    # Verify metrics are present
    for message in new_messages:
        if message.role in ["assistant", "tool"]:
            assert "metrics" in message.model_dump()
            if message.role == "assistant":
                assert "usage" in message.metrics
                assert "timing" in message.metrics
            if message.role == "tool":
                assert "timing" in message.metrics

@pytest.mark.asyncio
async def test_process_message_files(agent):
    """Test processing message files with attachments"""
    message = Message(role="user", content="Test with attachments")
    
    # Create a mock attachment with the content already set
    attachment = Attachment(
        id="test-attachment",
        filename="test.pdf",
        mime_type=None,
        size=100,
        storage_path="test/path",
        content=b"test content"  # Set the content directly
    )
    
    message.attachments = [attachment]
    
    with patch('magic.from_buffer', return_value='application/pdf'):
        await agent._process_message_files(message)
    
    assert attachment.mime_type == 'application/pdf'
    assert attachment.processed_content == {"content": "processed content"}

@pytest.mark.asyncio
async def test_process_message_files_with_error(agent):
    """Test processing message files with an error"""
    message = Message(role="user", content="Test with error")
    
    # Create a mock attachment that will raise an error when getting content
    attachment = Attachment(
        id="test-attachment",
        filename="test.doc",
        mime_type=None,
        size=100,
        storage_path="test/path",
        content=None  # This will cause an error when trying to process
    )
    
    message.attachments = [attachment]
    
    await agent._process_message_files(message)
    
    assert "Failed to process file" in attachment.processed_content["error"]

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs) 