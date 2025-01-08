import pytest
from unittest.mock import patch, MagicMock, create_autospec
from models.Agent import Agent
from models.Thread import Thread
from models.Message import Message
from utils.tool_runner import ToolRunner
from database.thread_store import ThreadStore
from prompts.AgentPrompt import AgentPrompt
from openai import OpenAI
from litellm import ModelResponse

@pytest.fixture
def mock_openai_client():
    mock_client = MagicMock(spec=OpenAI)
    mock_client.api_key = "test-key"
    mock_client._base_url = MagicMock()
    mock_client._base_url._uri_reference = "https://api.openai.com/v1"
    mock_chat = MagicMock()
    mock_client.chat = mock_chat
    mock_chat.completions = MagicMock()
    mock_chat.completions.create = MagicMock()
    return mock_client

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

@pytest.fixture
def mock_tool_runner():
    mock = create_autospec(ToolRunner, instance=True)
    mock.list_tools.return_value = ["test-tool"]
    mock.get_tool_description.return_value = "Test tool description"
    mock.get_tool_parameters.return_value = {"type": "object", "properties": {}}
    return mock

@pytest.fixture
def mock_thread_store():
    return create_autospec(ThreadStore, instance=True)

@pytest.fixture
def mock_prompt():
    mock = create_autospec(AgentPrompt, instance=True)
    mock.system_prompt.return_value = "Test system prompt"
    return mock

@pytest.fixture
def agent(mock_tool_runner, mock_thread_store, mock_prompt, mock_litellm):
    agent = Agent(
        model_name="gpt-4",
        temperature=0.5,
        context="test context",
        prompt=mock_prompt,
        tool_runner=mock_tool_runner,
        thread_store=mock_thread_store
    )
    return agent

def test_init(agent, mock_tool_runner):
    """Test Agent initialization"""
    assert agent.model_name == "gpt-4"
    assert agent.temperature == 0.5
    assert agent.context == "test context"
    assert len(agent.tools) == 1
    
    tool_def = agent.tools[0]
    assert tool_def["type"] == "function"
    assert tool_def["function"]["name"] == "test-tool"
    assert tool_def["function"]["description"] == "Test tool description"
    assert tool_def["function"]["parameters"] == {"type": "object", "properties": {}}

def test_go_thread_not_found(agent, mock_thread_store):
    """Test go() with non-existent thread"""
    mock_thread_store.get.return_value = None
    
    with pytest.raises(ValueError, match="Thread with ID test-conv not found"):
        agent.go("test-conv")

def test_go_max_recursion(agent, mock_thread_store):
    """Test go() with maximum recursion depth reached"""
    thread = Thread(id="test-conv", title="Test Thread")
    mock_thread_store.get.return_value = thread
    agent.current_recursion_depth = agent.max_tool_recursion
    
    result_thread, new_messages = agent.go("test-conv")
    
    assert len(new_messages) == 1
    assert new_messages[0].role == "assistant"
    assert new_messages[0].content == "Maximum tool recursion depth reached. Stopping further tool calls."
    mock_thread_store.save.assert_called_once_with(result_thread)

def test_go_no_tool_calls(agent, mock_thread_store, mock_prompt, mock_litellm):
    """Test go() with a response that doesn't include tool calls"""
    thread = Thread(id="test-conv", title="Test Thread")
    mock_thread_store.get.return_value = thread
    agent.current_recursion_depth = 0  # Reset recursion depth
    
    result_thread, new_messages = agent.go("test-conv")
    
    # Verify system prompt was added
    assert result_thread.messages[0].role == "system"
    assert result_thread.messages[0].content == "Test system prompt"
    
    # Verify assistant response was added
    assert result_thread.messages[1].role == "assistant"
    assert result_thread.messages[1].content == "Test response"
    
    # Verify new messages list is correct
    assert len(new_messages) == 2
    assert new_messages[0].role == "system"
    assert new_messages[1].role == "assistant"
    
    # Verify thread was saved
    mock_thread_store.save.assert_called_with(result_thread)
    
    # Verify recursion depth was reset
    assert agent.current_recursion_depth == 0

def test_go_with_tool_calls(agent, mock_thread_store, mock_prompt, mock_litellm):
    """Test go() with a response that includes tool calls"""
    thread = Thread(id="test-conv", title="Test Thread")
    mock_thread_store.get.return_value = thread
    agent.current_recursion_depth = 0  # Reset recursion depth
    
    # First response with tool call
    tool_call = MagicMock(
        id="test-call-id",
        function=MagicMock(
            name="test-tool",
            arguments='{"arg": "value"}'
        )
    )
    
    # Create proper mock responses that match litellm's response format
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
    
    # Set up mock to return different responses on subsequent calls
    mock_litellm.side_effect = [first_response, second_response]
    
    # Mock tool execution result
    agent.tool_runner.run_tool.return_value = "Tool result"
    
    result_thread, new_messages = agent.go("test-conv")
    
    # Verify messages were added in correct order
    messages = result_thread.messages
    assert len(messages) == 4  # system prompt + assistant + function + final response
    assert messages[0].role == "system"
    assert messages[1].role == "assistant"
    assert messages[1].content == "Test response with tool"
    assert messages[1].attributes["tool_calls"] == [tool_call]
    assert messages[2].role == "function"
    assert messages[2].content == "Tool result"
    assert messages[2].name == "test-tool"
    assert messages[2].attributes["tool_call_id"] == "test-call-id"
    assert messages[3].role == "assistant"
    assert messages[3].content == "Final response"
    
    # Verify new messages list contains all non-user messages
    assert len(new_messages) == 4
    assert [m.role for m in new_messages] == ["system", "assistant", "function", "assistant"]
    
    # Verify tool was executed
    agent.tool_runner.run_tool.assert_called_once_with(
        "test-tool",
        {"arg": "value"}
    )

def test_handle_tool_execution_error(agent):
    """Test _handle_tool_execution with error"""
    tool_call = MagicMock()
    tool_call.id = "test-call-id"
    tool_call.function.name = "test-tool"
    tool_call.function.arguments = '{"arg": "value"}'
    
    # Make tool execution raise an error
    agent.tool_runner.run_tool.side_effect = Exception("Test error")
    
    result = agent._handle_tool_execution(tool_call)
    
    assert result["tool_call_id"] == "test-call-id"
    assert result["name"] == "test-tool"
    assert result["content"] == "Error executing tool: Test error" 