"""Example of using Tyler with multiple MCP servers.

This example demonstrates how to use Tyler with multiple MCP servers.
"""
# Load environment variables and configure logging first
from dotenv import load_dotenv
load_dotenv()

from tyler.utils.logging import get_logger
logger = get_logger(__name__)

# Now import everything else
import asyncio
import os
import sys
from typing import List, Dict, Any

from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.mcp.utils import initialize_mcp_service, cleanup_mcp_service

# Add the parent directory to the path so we can import the example utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    """Run the example."""
    # Check for Brave API key
    brave_api_key = os.environ.get("BRAVE_API_KEY")
    if not brave_api_key:
        logger.warning("BRAVE_API_KEY environment variable not set. "
                      "Please set it to use the Brave Search API.")
        return
        
    logger.info("Initializing MCP service with multiple servers...")
    
    # Configure multiple MCP servers
    server_configs = [
        {
            "name": "brave",
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "startup_timeout": 5,
            "required": True,
            "env": {
                "BRAVE_API_KEY": brave_api_key
            }
        },
        {
            "name": "external",
            "transport": "sse",
            "url": "http://localhost:3000/v1",
            "required": False  # This server is optional (might not be running)
        }
    ]
    
    # Initialize the MCP service
    mcp_service = await initialize_mcp_service(server_configs)
    
    try:
        # Get the MCP tools for the agent
        mcp_tools = mcp_service.get_tools_for_agent(["brave", "external"])
        
        if not mcp_tools:
            logger.error("No tools discovered from any MCP server.")
            return
            
        logger.info(f"Discovered {len(mcp_tools)} tools from MCP servers.")
        
        # Create an agent with the MCP tools
        agent = Agent(
            name="Tyler",
            model_name="gpt-4o",
            tools=mcp_tools
        )
        
        # Create a thread
        thread = Thread()
        
        # Add a user message
        thread.add_message(Message(
            role="user",
            content="What can you tell me about the latest developments in renewable energy?"
        ))
        
        # Process the thread with streaming
        logger.info("Processing thread with streaming...")
        async for update in agent.go_stream(thread):
            if update.type.name == "CONTENT_CHUNK":
                print(update.data, end="", flush=True)
            elif update.type.name == "TOOL_MESSAGE":
                print(f"\n[Tool execution: {update.data['name']}]\n")
            elif update.type.name == "COMPLETE":
                print("\n\nProcessing complete!")
                
    finally:
        # Clean up the MCP service
        logger.info("Cleaning up MCP service...")
        await cleanup_mcp_service()


if __name__ == "__main__":
    asyncio.run(main()) 