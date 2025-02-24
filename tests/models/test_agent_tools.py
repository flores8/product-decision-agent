import pytest
from tyler.models.agent import Agent
from tyler.tools import TOOL_MODULES, TOOLS
from tyler.utils.tool_runner import tool_runner

@pytest.mark.asyncio
async def test_agent_loads_individual_tools():
    """Test that agent correctly loads tools when specifying individual modules"""
    # Test loading just web tools
    agent_web = Agent(
        model_name="gpt-4o",
        purpose="test",
        tools=["web"]
    )
    # Verify web tools are loaded
    web_tool_names = {tool['definition']['function']['name'] for tool in TOOL_MODULES['web']}
    agent_web_tools = {tool['function']['name'] for tool in agent_web._processed_tools}
    assert web_tool_names == agent_web_tools, f"Expected {web_tool_names}, got {agent_web_tools}"
    
    # Test loading just slack tools
    agent_slack = Agent(
        model_name="gpt-4o",
        purpose="test",
        tools=["slack"]
    )
    # Verify slack tools are loaded
    slack_tool_names = {tool['definition']['function']['name'] for tool in TOOL_MODULES['slack']}
    agent_slack_tools = {tool['function']['name'] for tool in agent_slack._processed_tools}
    assert slack_tool_names == agent_slack_tools, f"Expected {slack_tool_names}, got {agent_slack_tools}"

@pytest.mark.asyncio
async def test_agent_loads_multiple_tool_modules():
    """Test that agent correctly loads tools when specifying multiple modules"""
    agent = Agent(
        model_name="gpt-4o",
        purpose="test",
        tools=["web", "slack"]
    )
    
    # Get expected tools from both modules
    expected_tools = set()
    for module in ["web", "slack"]:
        module_tools = {tool['definition']['function']['name'] for tool in TOOL_MODULES[module]}
        expected_tools.update(module_tools)
    
    # Get actual tools loaded in agent
    agent_tools = {tool['function']['name'] for tool in agent._processed_tools}
    
    assert expected_tools == agent_tools, f"Expected {expected_tools}, got {agent_tools}"

@pytest.mark.asyncio
async def test_agent_loads_no_tools_by_default():
    """Test that agent loads no tools when none are specified"""
    agent = Agent(
        model_name="gpt-4o",
        purpose="test"
    )
    
    assert len(agent._processed_tools) == 0, "Expected no tools to be loaded by default"

@pytest.mark.asyncio
async def test_agent_tool_functionality():
    """Test that loaded tools are actually functional"""
    agent = Agent(
        model_name="gpt-4o",
        purpose="test",
        tools=["web"]
    )
    
    # Verify web tools exist in processed tools
    web_tools = [tool for tool in agent._processed_tools if tool['function']['name'].startswith('web-')]
    assert len(web_tools) > 0, "No web tools were loaded"
    
    # Verify the tools are properly registered in the global tool runner
    for tool in web_tools:
        tool_name = tool['function']['name']
        assert tool_name in tool_runner.tools, f"Tool {tool_name} not registered in tool runner" 