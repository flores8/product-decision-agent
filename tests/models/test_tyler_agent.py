import pytest
from unittest.mock import patch, MagicMock, create_autospec
from models.TylerAgent import TylerAgent
from models.conversation import Conversation
from models.message import Message
from utils.tool_runner import ToolRunner
from database.conversation_store import ConversationStore
from prompts.TylerPrompt import TylerPrompt

@pytest.fixture
def mock_tool_runner():
    mock = create_autospec(ToolRunner, instance=True)
    mock.list_tools.return_value = ["test-tool"]
    mock.get_tool_description.return_value = "Test tool description"
    mock.get_tool_parameters.return_value = {"type": "object", "properties": {}}
    return mock

@pytest.fixture
def mock_conversation_store():
    return create_autospec(ConversationStore, instance=True)

@pytest.fixture
def mock_prompt():
    mock = create_autospec(TylerPrompt, instance=True)
    mock.system_prompt.return_value = "Test system prompt"
    return mock

@pytest.fixture
def tyler_agent(mock_tool_runner, mock_conversation_store, mock_prompt):
    with patch('models.TylerAgent.ToolRunner', return_value=mock_tool_runner):
        agent = TylerAgent(
            model_name="test-model",
            temperature=0.5,
            context="test context",
            prompt=mock_prompt,
            tool_runner=mock_tool_runner,
            conversation_store=mock_conversation_store
        )
        return agent

def test_init(tyler_agent, mock_tool_runner):
    """Test TylerAgent initialization"""
    assert tyler_agent.model_name == "test-model"
    assert tyler_agent.temperature == 0.5
    assert tyler_agent.context == "test context"
    assert len(tyler_agent.tools) == 1
    
    tool_def = tyler_agent.tools[0]
    assert tool_def["type"] == "function"
    assert tool_def["function"]["name"] == "test-tool"
    assert tool_def["function"]["description"] == "Test tool description"
    assert tool_def["function"]["parameters"] == {"type": "object", "properties": {}}

def test_go_conversation_not_found(tyler_agent, mock_conversation_store):
    """Test go() with non-existent conversation"""
    mock_conversation_store.get.return_value = None
    
    with pytest.raises(ValueError, match="Conversation with ID test-conv not found"):
        tyler_agent.go("test-conv")

def test_go_max_recursion(tyler_agent, mock_conversation_store):
    """Test go() with maximum recursion depth reached"""
    conversation = Conversation(id="test-conv", title="Test Conversation")
    mock_conversation_store.get.return_value = conversation
    tyler_agent.current_recursion_depth = tyler_agent.max_tool_recursion
    
    tyler_agent.go("test-conv")
    
    messages = conversation.messages
    assert len(messages) == 1
    assert messages[0].role == "assistant"
    assert messages[0].content == "Maximum tool recursion depth reached. Stopping further tool calls."
    mock_conversation_store.save.assert_called_once_with(conversation)

@patch('models.TylerAgent.completion')
def test_go_no_tool_calls(mock_completion, tyler_agent, mock_conversation_store, mock_prompt):
    """Test go() with a response that doesn't include tool calls"""
    conversation = Conversation(id="test-conv", title="Test Conversation")
    mock_conversation_store.get.return_value = conversation
    tyler_agent.current_recursion_depth = 0  # Reset recursion depth
    
    mock_completion.return_value.choices = [
        MagicMock(message=MagicMock(
            content="Test response",
            tool_calls=None  # Explicitly set tool_calls to None
        ))
    ]
    
    tyler_agent.go("test-conv")
    
    # Verify system prompt was added
    assert conversation.messages[0].role == "system"
    assert conversation.messages[0].content == "Test system prompt"
    
    # Verify assistant response was added
    assert conversation.messages[1].role == "assistant"
    assert conversation.messages[1].content == "Test response"
    
    # Verify conversation was saved
    mock_conversation_store.save.assert_called_with(conversation)
    
    # Verify recursion depth was reset
    assert tyler_agent.current_recursion_depth == 0

@patch('models.TylerAgent.completion')
def test_go_with_tool_calls(mock_completion, tyler_agent, mock_conversation_store, mock_prompt):
    """Test go() with a response that includes tool calls"""
    conversation = Conversation(id="test-conv", title="Test Conversation")
    mock_conversation_store.get.return_value = conversation
    tyler_agent.current_recursion_depth = 0  # Reset recursion depth
    
    # First response with tool call
    tool_call = MagicMock()
    tool_call.id = "test-call-id"
    tool_call.function.name = "test-tool"
    tool_call.function.arguments = '{"arg": "value"}'
    
    # Set up mock to return different responses on subsequent calls
    mock_completion.side_effect = [
        # First call - return tool call
        MagicMock(choices=[
            MagicMock(
                message=MagicMock(
                    content="Test response with tool",
                    tool_calls=[tool_call]
                )
            )
        ]),
        # Second call - return final response without tool calls
        MagicMock(choices=[
            MagicMock(
                message=MagicMock(
                    content="Final response",
                    tool_calls=None
                )
            )
        ])
    ]
    
    # Mock tool execution result
    tyler_agent.tool_runner.run_tool.return_value = "Tool result"
    
    tyler_agent.go("test-conv")
    
    # Verify messages were added in correct order
    messages = conversation.messages
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
    
    # Verify tool was executed
    tyler_agent.tool_runner.run_tool.assert_called_once_with(
        "test-tool",
        {"arg": "value"}
    )
    
    # Verify recursion depth was reset
    assert tyler_agent.current_recursion_depth == 0

def test_handle_tool_execution_error(tyler_agent):
    """Test _handle_tool_execution with error"""
    tool_call = MagicMock()
    tool_call.id = "test-call-id"
    tool_call.function.name = "test-tool"
    tool_call.function.arguments = '{"arg": "value"}'
    
    # Make tool execution raise an error
    tyler_agent.tool_runner.run_tool.side_effect = Exception("Test error")
    
    result = tyler_agent._handle_tool_execution(tool_call)
    
    assert result["tool_call_id"] == "test-call-id"
    assert result["name"] == "test-tool"
    assert result["content"] == "Error executing tool: Test error" 