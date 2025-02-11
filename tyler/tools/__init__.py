"""
Tools package initialization.
"""
import importlib
import sys
import logging

logger = logging.getLogger(__name__)

# Initialize empty tool lists
WEB_TOOLS = []
SLACK_TOOLS = []
COMMAND_LINE_TOOLS = []
NOTION_TOOLS = []

# Try to import each tool module
def _import_tool_module(module_name):
    try:
        return importlib.import_module(f"tyler.tools.{module_name}")
    except ImportError as e:
        logger.warning(f"Could not import {module_name} tools: {str(e)}")
        return None

# Import tool modules
web_module = _import_tool_module("web")
slack_module = _import_tool_module("slack")
command_line_module = _import_tool_module("command_line")
notion_module = _import_tool_module("notion")

# Update tool lists if modules were imported successfully
if web_module:
    WEB_TOOLS = getattr(web_module, "WEB_TOOLS", [])
if slack_module:
    SLACK_TOOLS = getattr(slack_module, "SLACK_TOOLS", [])
if command_line_module:
    COMMAND_LINE_TOOLS = getattr(command_line_module, "COMMAND_LINE_TOOLS", [])
if notion_module:
    NOTION_TOOLS = getattr(notion_module, "NOTION_TOOLS", [])

# Export all tool definitions
__all__ = [
    'WEB_TOOLS',
    'SLACK_TOOLS',
    'COMMAND_LINE_TOOLS',
    'NOTION_TOOLS',
]

# Create a mapping of tool module names to their tool lists
TOOL_MODULES = {
    'web': WEB_TOOLS,
    'slack': SLACK_TOOLS,
    'command_line': COMMAND_LINE_TOOLS,
    'notion': NOTION_TOOLS,
} 