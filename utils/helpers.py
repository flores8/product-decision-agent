import os
import importlib
from typing import List, Any

def get_all_tools() -> List[Any]:
    """
    Dynamically loads and combines all tool definitions from Python files in the tools directory.
    
    Returns:
        List[Any]: Combined list of all tools found in the directory
    """
    all_tools = []
    
    # Get the absolute path to the tools directory
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tools_path = os.path.join(base_path, "tools")
    
    # Ensure the directory exists
    if not os.path.exists(tools_path):
        return all_tools
        
    # Iterate through Python files in the tools directory
    for filename in os.listdir(tools_path):
        if filename.endswith('.py') and not filename.startswith('__'):
            # Convert filename to module path (e.g., 'tools.notion')
            module_name = f"tools.{filename[:-3]}"
            
            try:
                # Import the module
                module = importlib.import_module(module_name)
                
                # Look for tool definitions (conventionally named *_TOOLS)
                for attr_name in dir(module):
                    if attr_name.endswith('_TOOLS'):
                        tools = getattr(module, attr_name)
                        
                        # Handle both list and dict tool definitions
                        if isinstance(tools, dict):
                            all_tools.extend(tools.values())
                        elif isinstance(tools, list):
                            all_tools.extend(tools)
                            
            except Exception as e:
                print(f"Error loading tools from {filename}: {str(e)}")
                
    return all_tools 