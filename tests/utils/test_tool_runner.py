import pytest
from tyler.utils.tool_runner import ToolRunner
from pathlib import Path
import os
from unittest.mock import patch, MagicMock

@pytest.fixture
def tool_runner():
    return ToolRunner()

@pytest.fixture
def sample_tool():
    return {
        'definition': {
            'type': 'function',
            'function': {
                'name': 'test_tool',
                'description': 'A test tool',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'param1': {'type': 'string'}
                    },
                    'required': ['param1']
                }
            }
        },
        'implementation': lambda param1: f"Result: {param1}"
    }

def test_register_tool(tool_runner, sample_tool):
    """Test registering a new tool"""
    tool_runner.register_tool('test_tool', sample_tool['implementation'])
    assert 'test_tool' in tool_runner.tools
    assert 'implementation' in tool_runner.tools['test_tool']

def test_load_tool_module(tool_runner):
    """Test loading tools from a module"""
    # Create a mock module with tools
    mock_module = MagicMock()
    mock_module.TEST_TOOLS = [
        {
            'definition': {
                'type': 'function',
                'function': {
                    'name': 'mock_tool',
                    'description': 'A mock tool',
                    'parameters': {}
                }
            },
            'implementation': lambda: "mock result"
        }
    ]
    
    with patch('importlib.import_module', return_value=mock_module):
        loaded_tools = tool_runner.load_tool_module('test')
        assert len(loaded_tools) == 1
        assert loaded_tools[0]['function']['name'] == 'mock_tool'
        assert 'mock_tool' in tool_runner.tools

def test_run_tool(tool_runner, sample_tool):
    """Test running a registered tool"""
    tool_runner.register_tool('test_tool', sample_tool['implementation'])
    result = tool_runner.run_tool('test_tool', {'param1': 'hello'})
    assert result == 'Result: hello'

def test_run_tool_with_invalid_name(tool_runner):
    """Test running a nonexistent tool"""
    with pytest.raises(ValueError) as exc_info:
        tool_runner.run_tool("nonexistent-tool", {})
    assert "Tool 'nonexistent-tool' not found" in str(exc_info.value)

def test_get_tool_description(tool_runner, sample_tool):
    """Test getting tool descriptions"""
    tool_runner.tools['test_tool'] = {
        'definition': sample_tool['definition']['function'],
        'implementation': sample_tool['implementation']
    }
    desc = tool_runner.get_tool_description('test_tool')
    assert desc == 'A test tool'
    
    # Test invalid tool
    desc = tool_runner.get_tool_description('nonexistent-tool')
    assert desc is None

def test_list_tools(tool_runner, sample_tool):
    """Test listing available tools"""
    tool_runner.tools['test_tool'] = {
        'definition': sample_tool['definition']['function'],
        'implementation': sample_tool['implementation']
    }
    tools = tool_runner.list_tools()
    assert isinstance(tools, list)
    assert 'test_tool' in tools

def test_get_tool_parameters(tool_runner, sample_tool):
    """Test getting tool parameter schemas"""
    tool_runner.tools['test_tool'] = {
        'definition': sample_tool['definition']['function'],
        'implementation': sample_tool['implementation']
    }
    params = tool_runner.get_tool_parameters('test_tool')
    assert isinstance(params, dict)
    assert 'properties' in params
    assert 'param1' in params['properties']
    
    # Test invalid tool
    params = tool_runner.get_tool_parameters('nonexistent-tool')
    assert params is None

def test_get_tools_for_chat_completion(tool_runner, sample_tool):
    """Test getting tools in chat completion format"""
    tool_runner.tools['test_tool'] = {
        'definition': sample_tool['definition']['function'],
        'implementation': sample_tool['implementation']
    }
    tools = tool_runner.get_tools_for_chat_completion()
    assert isinstance(tools, list)
    assert len(tools) == 1
    assert tools[0]['type'] == 'function'
    assert tools[0]['function']['name'] == 'test_tool'
    assert tools[0]['function']['description'] == 'A test tool'

def test_execute_tool_call(tool_runner, sample_tool):
    """Test executing a tool call"""
    tool_runner.tools['test_tool'] = {
        'definition': sample_tool['definition']['function'],
        'implementation': sample_tool['implementation']
    }
    
    # Create a mock tool call object
    tool_call = MagicMock()
    tool_call.id = 'test_id'
    tool_call.function.name = 'test_tool'
    tool_call.function.arguments = '{"param1": "test"}'
    
    result = tool_runner.execute_tool_call(tool_call)
    assert result['tool_call_id'] == 'test_id'
    assert result['name'] == 'test_tool'
    assert result['content'] == 'Result: test' 