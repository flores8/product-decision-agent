import pytest
from unittest.mock import patch, MagicMock, create_autospec
from models.Agent import Agent, AgentPrompt
from models.Thread import Thread
from models.Message import Message
from utils.tool_runner import tool_runner
from database.thread_store import ThreadStore
from openai import OpenAI
from litellm import ModelResponse

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

@pytest.fixture
def agent(mock_thread_store, mock_prompt, mock_litellm):
    with patch('models.Agent.tool_runner', mock_tool_runner):
        agent = Agent(
            model_name="gpt-4",
            temperature=0.5,
            purpose="test purpose",
            notes="test notes",
            prompt=mock_prompt,
            thread_store=mock_thread_store
        )
        return agent

def test_init(agent):
    """Test Agent initialization"""
    assert agent.model_name == "gpt-4"
    assert agent.temperature == 0.5
    assert agent.purpose == "test purpose"
    assert agent.notes == "test notes"
    assert len(agent.tools) == 0  # Tools are now handled by tool_runner module

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

def test_go_no_tool_calls(agent, mock_thread_store, mock_prompt):
    """Test go() with a response that doesn't include tool calls"""
    thread = Thread(id="test-conv", title="Test Thread")
    thread.ensure_system_prompt("Test system prompt")
    mock_thread_store.get.return_value = thread
    agent.current_recursion_depth = 0
    
    mock_response = MagicMock(
        choices=[MagicMock(
            message=MagicMock(
                content="Test response",
                tool_calls=None
            )
        )]
    )
    
    with patch('models.Agent.completion', return_value=mock_response):
        result_thread, new_messages = agent.go("test-conv")
    
    assert result_thread.messages[0].role == "system"
    assert result_thread.messages[0].content == "Test system prompt"
    assert result_thread.messages[1].role == "assistant"
    assert result_thread.messages[1].content == "Test response"
    assert len(new_messages) == 1
    assert new_messages[0].role == "assistant"
    mock_thread_store.save.assert_called_with(result_thread)
    assert agent.current_recursion_depth == 0

def test_go_with_tool_calls(agent, mock_thread_store, mock_prompt):
    """Test go() with a response that includes tool calls"""
    thread = Thread(id="test-conv", title="Test Thread")
    thread.ensure_system_prompt("Test system prompt")
    mock_thread_store.get.return_value = thread
    agent.current_recursion_depth = 0
    
    tool_call = MagicMock(
        id="test-call-id",
        function=MagicMock(
            name="test-tool",
            arguments='{"arg": "value"}'
        )
    )
    
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
    
    with patch('models.Agent.completion', mock_completion), \
         patch('models.Agent.tool_runner') as patched_tool_runner:
        patched_tool_runner.execute_tool_call.return_value = {
            "name": "test-tool",
            "content": "Tool result"
        }
        
        result_thread, new_messages = agent.go("test-conv")
    
    messages = result_thread.messages
    assert len(messages) == 4
    assert messages[0].role == "system"
    assert messages[1].role == "assistant"
    assert messages[1].content == "Test response with tool"
    assert messages[1].tool_calls == [tool_call]
    assert messages[2].role == "tool"
    assert messages[2].content == "Tool result"
    assert messages[2].name == "test-tool"
    assert messages[2].tool_call_id == "test-call-id"
    assert messages[3].role == "assistant"
    assert messages[3].content == "Final response"
    
    assert len(new_messages) == 3
    assert [m.role for m in new_messages] == ["assistant", "tool", "assistant"]

def test_handle_tool_execution(agent, mock_tool_runner):
    """Test _handle_tool_execution"""
    tool_call = MagicMock()
    tool_call.id = "test-call-id"
    tool_call.function.name = "test-tool"
    tool_call.function.arguments = '{"arg": "value"}'
    
    with patch('models.Agent.tool_runner') as patched_tool_runner:
        patched_tool_runner.execute_tool_call.return_value = {
            "name": "test-tool",
            "content": "Tool result"
        }
        
        result = agent._handle_tool_execution(tool_call)
    
    assert result["name"] == "test-tool"
    assert result["content"] == "Tool result" 