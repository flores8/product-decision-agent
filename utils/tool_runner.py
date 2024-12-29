import importlib
import inspect
from typing import Dict, Any, List, Optional
import os
import glob
from pathlib import Path
import weave

class ToolRunner:
    def __init__(self):
        self.tools = {}
        self._load_tools()

    def _load_tools(self) -> None:
        """
        Dynamically loads all tools from the tools directory.
        Each tool should be a Python file with one or more functions decorated with @weave.op
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
                            if isinstance(tool, dict) and tool.get('type') == 'function':
                                func_name = tool['function']['name']
                                self.tools[func_name] = {
                                    'module': module,
                                    'definition': tool['function']
                                }
            except Exception as e:
                print(f"Error loading tool file {tool_file}: {str(e)}")

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
        module = tool['module']
        
        # Find the function in the module
        func_name = tool_name.split('-')[1] if '-' in tool_name else tool_name
        if not hasattr(module, func_name):
            raise ValueError(f"Function '{func_name}' not found in module")
            
        func = getattr(module, func_name)
        
        # Execute the tool
        try:
            return func(**parameters)
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