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
import logging

logger = logging.getLogger(__name__)

class ToolRunner:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, name: str, implementation: Union[Callable, Coroutine]) -> None:
        """
        Register a new tool implementation.
        
        Args:
            name: The name of the tool
            implementation: The function or coroutine that implements the tool
        """
        if name in self.tools:
            self.tools[name]['implementation'] = implementation
        else:
            # Create a new tool entry if it doesn't exist
            self.tools[name] = {
                'implementation': implementation,
                'definition': {},  # Empty definition, will be filled later
                'is_async': inspect.iscoroutinefunction(implementation)
            }

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
            logger.info(f"Attempting to load tool module: {module_path}")
            
            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                logger.error(f"Failed to import module {module_path}: {str(e)}")
                # Try to import from tyler.tools directly
                try:
                    from tyler.tools import TOOL_MODULES
                    if module_name in TOOL_MODULES:
                        logger.info(f"Found tools for {module_name} in TOOL_MODULES")
                        tools_list = TOOL_MODULES[module_name]
                        loaded_tools = []
                        for tool in tools_list:
                            if not isinstance(tool, dict) or 'definition' not in tool or 'implementation' not in tool:
                                logger.warning(f"Tool in {module_name} has invalid format")
                                continue
                                
                            if tool['definition'].get('type') != 'function':
                                logger.warning(f"Tool in {module_name} is not a function type")
                                continue
                                
                            func_name = tool['definition']['function']['name']
                            implementation = tool['implementation']
                            self.tools[func_name] = {
                                'definition': tool['definition']['function'],
                                'implementation': implementation,
                                'is_async': inspect.iscoroutinefunction(implementation)
                            }
                            loaded_tools.append(tool['definition'])
                        return loaded_tools
                    else:
                        logger.error(f"Module {module_name} not found in TOOL_MODULES")
                        return []
                except ImportError as e2:
                    logger.error(f"Failed to import TOOL_MODULES: {str(e2)}")
                    return []
            
            loaded_tools = []
            # Look for tool definitions (lists ending in _TOOLS)
            for attr_name in dir(module):
                if attr_name.endswith('_TOOLS'):
                    logger.info(f"Found tool list: {attr_name} in {module_path}")
                    tools_list = getattr(module, attr_name)
                    for tool in tools_list:
                        if not isinstance(tool, dict) or 'definition' not in tool or 'implementation' not in tool:
                            logger.warning(f"Tool in {module_path} has invalid format")
                            continue
                            
                        if tool['definition'].get('type') != 'function':
                            logger.warning(f"Tool in {module_path} is not a function type")
                            continue
                            
                        func_name = tool['definition']['function']['name']
                        implementation = tool['implementation']
                        self.tools[func_name] = {
                            'definition': tool['definition']['function'],
                            'implementation': implementation,
                            'is_async': inspect.iscoroutinefunction(implementation)
                        }
                        loaded_tools.append(tool['definition'])
                        logger.info(f"Loaded tool: {func_name}")
                        
            return loaded_tools
        except Exception as e:
            logger.error(f"Error loading tool module {module_name}: {str(e)}", exc_info=True)
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
            if tool_name in self.tools and self.tools[tool_name].get('is_async', False):
                result = await self.run_tool_async(tool_name, tool_args)
            else:
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