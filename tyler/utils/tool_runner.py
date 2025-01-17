import importlib
import inspect
from typing import Dict, Any, List, Optional, Callable
import os
import glob
from pathlib import Path
import weave
import json

class ToolRunner:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._load_tools()

    def _load_tools(self) -> None:
        """
        Dynamically loads all tools from the tools directory.
        Each tool should be defined with a definition and implementation.
        """
        tools_dir = Path(__file__).parent.parent / 'tools'
        
        # Get all Python files in the tools directory
        tool_files = glob.glob(str(tools_dir / '*.py'))
        
        for tool_file in tool_files:
            try:
                # Convert file path to module path
                module_name = os.path.splitext(os.path.basename(tool_file))[0]
                module_path = f"tools.{module_name}"
                
                # Import the module
                module = importlib.import_module(module_path)
                
                # Look for tool definitions (lists ending in _TOOLS)
                for attr_name in dir(module):
                    if attr_name.endswith('_TOOLS'):
                        tools_list = getattr(module, attr_name)
                        for tool in tools_list:
                            if not isinstance(tool, dict) or 'definition' not in tool or 'implementation' not in tool:
                                print(f"Warning: Tool in {module_path} has invalid format")
                                continue
                                
                            if tool['definition'].get('type') != 'function':
                                print(f"Warning: Tool in {module_path} is not a function type")
                                continue
                                
                            func_name = tool['definition']['function']['name']
                            self.tools[func_name] = {
                                'definition': tool['definition']['function'],
                                'implementation': tool['implementation']
                            }
            except Exception as e:
                print(f"Error loading tool file {tool_file}: {str(e)}")

    def register_tool(self, name: str, implementation: Callable) -> None:
        """
        Register a new tool implementation.
        
        Args:
            name: The name of the tool
            implementation: The function that implements the tool
        """
        if name in self.tools:
            self.tools[name]['implementation'] = implementation
        else:
            print(f"Warning: Tool '{name}' not found in definitions")

    @weave.op()
    def run_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Executes a tool by name with the given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Dictionary of parameters to pass to the tool
            
        Returns:
            The result of the tool execution
            
        Raises:
            ValueError: If tool_name is not found or parameters are invalid
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
            
        tool = self.tools[tool_name]
        if 'implementation' not in tool:
            raise ValueError(f"Implementation for tool '{tool_name}' not found")
            
        # Execute the tool
        try:
            return tool['implementation'](**parameters)
        except Exception as e:
            raise ValueError(f"Error executing tool '{tool_name}': {str(e)}")

    def get_tool_description(self, tool_name: str) -> Optional[str]:
        """Returns the description of a tool if it exists."""
        if tool_name in self.tools:
            return self.tools[tool_name]['definition'].get('description')
        return None

    def list_tools(self) -> List[str]:
        """Returns a list of all available tool names."""
        return list(self.tools.keys())

    def get_tool_parameters(self, tool_name: str) -> Optional[Dict]:
        """Returns the parameter schema for a tool if it exists."""
        if tool_name in self.tools:
            return self.tools[tool_name]['definition'].get('parameters')
        return None 

    def get_tools_for_chat_completion(self) -> List[dict]:
        """Returns tools in the format needed for chat completion."""
        tools = []
        for tool_name in self.list_tools():
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": self.get_tool_description(tool_name),
                    "parameters": self.get_tool_parameters(tool_name)
                }
            }
            tools.append(tool_def)
        return tools

    @weave.op()
    def execute_tool_call(self, tool_call) -> dict:
        """
        Execute a tool call and return formatted result for chat completion.
        
        Args:
            tool_call: The tool call object from the model response
            
        Returns:
            dict: Formatted result in chat completion format
        """
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        
        try:
            result = self.run_tool(tool_name, tool_args)
            return {
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": str(result)
            }
        except Exception as e:
            return {
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": f"Error executing tool: {str(e)}"
            }

# Create a shared instance
tool_runner = ToolRunner() 