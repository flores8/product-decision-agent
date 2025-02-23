import importlib
import inspect
from typing import Dict, Any, List, Optional, Callable, Union, Coroutine
import os
import glob
from pathlib import Path
import weave
import json
import asyncio
from functools import wraps
from tyler.utils.logging import get_logger

# Get configured logger
logger = get_logger(__name__)

class ToolRunner:
    def __init__(self):
        self.tools = {}  # name -> {implementation, is_async, definition}
        self.tool_attributes = {}  # name -> tool attributes

    def register_tool(self, name: str, implementation: Union[Callable, Coroutine], definition: Optional[Dict] = None) -> None:
        """
        Register a new tool implementation.
        
        Args:
            name: The name of the tool
            implementation: The function or coroutine that implements the tool
            definition: Optional OpenAI function definition
        """
        self.tools[name] = {
            'implementation': implementation,
            'is_async': inspect.iscoroutinefunction(implementation),
            'definition': definition
        }
        
    def register_tool_attributes(self, name: str, attributes: Dict[str, Any]) -> None:
        """
        Register optional tool-specific attributes.
        
        Args:
            name: The name of the tool
            attributes: Dictionary of tool-specific attributes
        """
        self.tool_attributes[name] = attributes
        
    def get_tool_attributes(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get tool-specific attributes if they exist.
        
        Args:
            name: The name of the tool
            
        Returns:
            Optional dictionary of tool attributes. None if no attributes were set.
        """
        return self.tool_attributes.get(name)
        
    def get_tool_definition(self, name: str) -> Optional[Dict[str, Any]]:
        """Get OpenAI function definition for a tool"""
        tool = self.tools.get(name)
        return tool['definition'] if tool else None

    @weave.op()
    def run_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Executes a synchronous tool by name with the given parameters.
        
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
            
        if tool.get('is_async', False):
            raise ValueError(f"Tool '{tool_name}' is async and must be run with run_tool_async")
            
        # Execute the tool
        try:
            return tool['implementation'](**parameters)
        except Exception as e:
            raise ValueError(f"Error executing tool '{tool_name}': {str(e)}")

    @weave.op()
    async def run_tool_async(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """
        Executes an async tool by name with the given parameters.
        
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
            if tool.get('is_async', False):
                return await tool['implementation'](**parameters)
            else:
                # Run sync tools in a thread pool
                return await asyncio.to_thread(tool['implementation'], **parameters)
        except Exception as e:
            raise ValueError(f"Error executing tool '{tool_name}': {str(e)}")

    def load_tool_module(self, module_name: str) -> List[dict]:
        """
        Load tools from a specific module in the tools directory.
        
        Args:
            module_name: Name of the module to load (e.g., 'web', 'slack')
            
        Returns:
            List of loaded tool definitions
        """
        try:
            # Import the module using the full package path
            module_path = f"tyler.tools.{module_name}"
            logger.debug(f"Loading module {module_path}")
            
            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                logger.error(f"Import failed: {str(e)}")
                # Try to import from tyler.tools directly
                try:
                    from tyler.tools import TOOL_MODULES
                    if module_name in TOOL_MODULES:
                        tools_list = TOOL_MODULES[module_name]
                        loaded_tools = []
                        for tool in tools_list:
                            if not isinstance(tool, dict) or 'definition' not in tool or 'implementation' not in tool:
                                logger.warning(f"Invalid tool format in {module_name}")
                                continue
                                
                            if tool['definition'].get('type') != 'function':
                                logger.warning(f"Tool in {module_name} is not a function type")
                                continue
                                
                            func_name = tool['definition']['function']['name']
                            implementation = tool['implementation']
                            
                            # Register the tool with its implementation and definition
                            self.tools[func_name] = {
                                'implementation': implementation,
                                'is_async': inspect.iscoroutinefunction(implementation),
                                'definition': tool['definition']['function']
                            }
                            
                            # Register any attributes if present at top level
                            if 'attributes' in tool:
                                self.tool_attributes[func_name] = tool['attributes']
                                
                            # Add only the OpenAI function definition
                            loaded_tools.append({
                                "type": "function",
                                "function": tool['definition']['function']
                            })
                            logger.debug(f"Loaded tool: {func_name}")
                        return loaded_tools
                    else:
                        logger.error(f"Module not found in TOOL_MODULES")
                        return []
                except ImportError as e2:
                    logger.error(f"Failed to import TOOL_MODULES")
                    return []
            
            loaded_tools = []
            # Look for TOOLS attribute directly
            if hasattr(module, 'TOOLS'):
                tools_list = getattr(module, 'TOOLS')
                for tool in tools_list:
                    if not isinstance(tool, dict) or 'definition' not in tool or 'implementation' not in tool:
                        logger.warning(f"Invalid tool format")
                        continue
                        
                    if tool['definition'].get('type') != 'function':
                        logger.warning(f"Tool in {module_name} is not a function type")
                        continue
                        
                    func_name = tool['definition']['function']['name']
                    implementation = tool['implementation']
                    
                    # Register the tool with its implementation and definition
                    self.tools[func_name] = {
                        'implementation': implementation,
                        'is_async': inspect.iscoroutinefunction(implementation),
                        'definition': tool['definition']['function']
                    }
                    
                    # Register any attributes if present at top level
                    if 'attributes' in tool:
                        self.tool_attributes[func_name] = tool['attributes']
                        
                    # Add only the OpenAI function definition
                    loaded_tools.append({
                        "type": "function",
                        "function": tool['definition']['function']
                    })
                    logger.debug(f"Loaded tool: {func_name}")
            else:
                logger.warning(f"No TOOLS attribute found in module {module_name}")
                    
            return loaded_tools
        except Exception as e:
            logger.error(f"Error loading module: {str(e)}")
            return []

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
    async def execute_tool_call(self, tool_call) -> dict:
        """Execute a tool call and return the result in the expected format."""
        logger.debug(f"Executing tool call: {tool_call}")
        
        # Get tool name and arguments
        tool_name = getattr(tool_call.function, 'name', None)
        logger.debug(f"Tool name: {tool_name}")
        logger.debug(f"Available tools: {list(self.tools.keys())}")
        
        if not tool_name:
            raise ValueError("Tool call missing function name")
            
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}")
            
        tool = self.tools[tool_name]
        logger.debug(f"Found tool implementation: {tool}")
        
        # Parse arguments
        try:
            arguments = json.loads(tool_call.function.arguments)
            logger.debug(f"Parsed arguments: {arguments}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in tool arguments: {e}")
            
        try:
            if tool['is_async']:
                result = await tool['implementation'](**arguments)
            else:
                result = await asyncio.to_thread(tool['implementation'], **arguments)
                
            logger.debug(f"Tool execution result: {result}")
            return {
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": str(result)
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            raise

# Create a shared instance
tool_runner = ToolRunner() 