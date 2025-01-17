import os
import importlib
from typing import List, Any, Optional, Union
import weave

@weave.op(name="helpers-get_tools")
def get_tools(tool_modules: Optional[Union[str, List[str]]] = None) -> List[Any]:
    """
    Dynamically loads and combines tool definitions from Python files in the tools directory.
    
    Args:
        tool_modules: Optional string or list of strings specifying which tool modules to load.
                     If None, loads all tools. Example: "notion" or ["notion", "slack"]
    
    Returns:
        List[Any]: Combined list of requested tools found in the directory
    """
    all_tools = []
    tool_names = set()  # To track duplicate tools
    
    # Get the absolute path to the tools directory
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tools_path = os.path.join(base_path, "tools")
    
    # Ensure the directory exists
    if not os.path.exists(tools_path):
        return all_tools
        
    # Convert single string to list for consistent processing
    if isinstance(tool_modules, str):
        tool_modules = [tool_modules]
        
    # Iterate through Python files in the tools directory
    for filename in os.listdir(tools_path):
        if filename.endswith('.py') and not filename.startswith('__'):
            module_base_name = filename[:-3]
            
            # Skip if specific modules were requested and this isn't one of them
            if tool_modules and module_base_name not in tool_modules:
                continue
                
            # Convert filename to module path (e.g., 'tools.notion')
            module_name = f"tools.{module_base_name}"
            
            try:
                # Import the module
                module = importlib.import_module(module_name)
                
                # Look for tool definitions (conventionally named *_TOOLS)
                for attr_name in dir(module):
                    if attr_name.endswith('_TOOLS'):
                        tools = getattr(module, attr_name)
                        
                        # Handle both list and dict tool definitions
                        if isinstance(tools, dict):
                            for tool in tools.values():
                                tool_name = tool["function"]["name"]
                                if tool_name not in tool_names:
                                    tool_names.add(tool_name)
                                    all_tools.append(tool)
                        elif isinstance(tools, list):
                            for tool in tools:
                                tool_name = tool["function"]["name"]
                                if tool_name not in tool_names:
                                    tool_names.add(tool_name)
                                    all_tools.append(tool)
                            
            except Exception as e:
                print(f"Error loading tools from {filename}: {str(e)}")
                
    return all_tools 