import pytest
from unittest.mock import patch, MagicMock
from models.TylerModel import TylerModel
from utils.tool_runner import ToolRunner
from prompts.AgentPrompt import AgentPrompt
import os
import openai

@pytest.fixture(autouse=True)
def mock_litellm():
    """Mock litellm completion"""
    with patch('litellm.completion') as mock_litellm:
        yield mock_litellm

@pytest.fixture
def mock_tool_runner():
    """Fixture to provide a mock tool runner"""
    return MagicMock(spec=ToolRunner)

@pytest.fixture
def tyler_model(mock_tool_runner):
    """Fixture to provide a TylerModel instance with mocked dependencies"""
    model = TylerModel()
    model.tool_runner = mock_tool_runner
    return model

def test_tyler_model_init():
    """Test TylerModel initialization with default values"""
    model = TylerModel()
    assert model.model_name == "gpt-4o"
    assert model.temperature == 0.7
    assert model.context == ""
    assert model.max_tool_recursion == 10
    assert isinstance(model.tool_runner, ToolRunner)
    assert isinstance(model.prompt, AgentPrompt)

def test_handle_tool_execution_success(tyler_model, mock_tool_runner):
    """Test successful tool execution"""
    # Setup mock tool call
    tool_call = MagicMock()
    tool_call.function.name = "test_tool"
    tool_call.function.arguments = '{"arg": "value"}'
    tool_call.id = "test_id"
    
    # Setup mock tool result
    mock_tool_runner.run_tool.return_value = "tool result"
    
    result = tyler_model._handle_tool_execution(tool_call)
    
    assert result["role"] == "tool"
    assert result["tool_call_id"] == "test_id"
    assert result["name"] == "test_tool"
    assert result["content"] == "tool result"
    
    mock_tool_runner.run_tool.assert_called_once_with(
        "test_tool", 
        {"arg": "value"}
    )

def test_handle_tool_execution_error(tyler_model, mock_tool_runner):
    """Test tool execution with error"""
    tool_call = MagicMock()
    tool_call.function.name = "test_tool"
    tool_call.function.arguments = '{"arg": "value"}'
    tool_call.id = "test_id"
    
    mock_tool_runner.run_tool.side_effect = Exception("Tool error")
    
    result = tyler_model._handle_tool_execution(tool_call)
    
    assert result["role"] == "tool"
    assert result["tool_call_id"] == "test_id"
    assert result["name"] == "test_tool"
    assert "Error executing tool: Tool error" in result["content"]

def test_process_response_no_tools(mock_litellm, tyler_model):
    """Test processing response without tool calls"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message={
                "content": "Test response",
                "role": "assistant"
            }
        )
    ]
    
    result = tyler_model._process_response(mock_response, [], 0)
    assert result == "Test response"

def test_process_response_with_tools(mock_litellm, tyler_model):
    """Test processing response with tool calls"""
    # First response with tool calls
    mock_tool_response = MagicMock()
    mock_tool_response.choices = [
        MagicMock(
            message={
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "function": {
                        "name": "test_tool",
                        "arguments": '{"arg": "value"}'
                    },
                    "id": "test_id"
                }]
            }
        )
    ]
    
    # Second response after tool execution
    mock_final_response = MagicMock()
    mock_final_response.choices = [
        MagicMock(
            message={
                "role": "assistant",
                "content": "Final response"
            }
        )
    ]
    
    mock_litellm.return_value = mock_final_response
    tyler_model.tool_runner.run_tool.return_value = "tool result"
    
    result = tyler_model._process_response(mock_tool_response, [], 0)
    assert result == "Final response"
    mock_litellm.assert_called_once_with(
        model=tyler_model.model_name,
        messages=mock.ANY,
        temperature=tyler_model.temperature,
        tools=mock.ANY
    )

def test_process_response_max_recursion(mock_litellm, tyler_model):
    """Test processing response hitting max recursion depth"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message={
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "function": {
                        "name": "test_tool",
                        "arguments": '{"arg": "value"}'
                    },
                    "id": "test_id"
                }]
            }
        )
    ]
    
    result = tyler_model._process_response(mock_response, [], 10)
    assert "Max tool recursion depth reached" in result

def test_predict_with_system_prompt(mock_litellm, tyler_model):
    """Test prediction with system prompt addition"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message={
                "role": "assistant",
                "content": "Test response"
            }
        )
    ]
    mock_litellm.return_value = mock_response
    
    messages = [{"role": "user", "content": "test"}]
    result = tyler_model.predict(messages)
    
    assert result == "Test response"
    mock_litellm.assert_called_once_with(
        model=tyler_model.model_name,
        messages=[{"role": "system", "content": tyler_model.prompt.system_prompt("")}] + messages,
        temperature=tyler_model.temperature,
        tools=mock.ANY
    )

def test_predict_with_existing_system_prompt(mock_litellm, tyler_model):
    """Test prediction with existing system prompt"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message={
                "role": "assistant",
                "content": "Test response"
            }
        )
    ]
    mock_litellm.return_value = mock_response
    
    messages = [
        {"role": "system", "content": "existing system prompt"},
        {"role": "user", "content": "test"}
    ]
    
    result = tyler_model.predict(messages)
    
    assert result == "Test response"
    mock_litellm.assert_called_once_with(
        model=tyler_model.model_name,
        messages=messages,
        temperature=tyler_model.temperature,
        tools=mock.ANY
    )

def test_predict_with_context(mock_litellm, tyler_model):
    """Test prediction with context"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message={
                "role": "assistant",
                "content": "Test response"
            }
        )
    ]
    mock_litellm.return_value = mock_response
    
    tyler_model.context = "test context"
    messages = [{"role": "user", "content": "test"}]
    result = tyler_model.predict(messages)
    
    assert result == "Test response"
    mock_litellm.assert_called_once_with(
        model=tyler_model.model_name,
        messages=[{"role": "system", "content": tyler_model.prompt.system_prompt("test context")}] + messages,
        temperature=tyler_model.temperature,
        tools=mock.ANY
    )

def test_predict_with_tools(mock_litellm, tyler_model):
    """Test prediction with tools enabled"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message={
                "role": "assistant",
                "content": "Test response"
            }
        )
    ]
    mock_litellm.return_value = mock_response
    
    messages = [{"role": "user", "content": "test"}]
    result = tyler_model.predict(messages)
    
    assert result == "Test response"
    mock_litellm.assert_called_once_with(
        model=tyler_model.model_name,
        messages=[{"role": "system", "content": tyler_model.prompt.system_prompt("")}] + messages,
        temperature=tyler_model.temperature,
        tools=mock.ANY
    ) 