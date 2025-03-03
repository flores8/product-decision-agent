"""Detailed example of using Tyler with the Brave Search MCP server.

This example demonstrates how to:
1. Configure and start the Brave Search MCP server
2. Connect to the server and discover tools
3. Create a Tyler agent with the discovered tools
4. Use the agent to perform searches and process the results

Requirements:
- MCP Python SDK: pip install mcp>=1.3.0
- Brave Search API key: https://brave.com/search/api/
  (Set as BRAVE_API_KEY environment variable)
- Node.js and NPM installed (for running the Brave Search MCP server)
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
from tyler.mcp.service import MCPService

# Add the parent directory to the path so we can import the example utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def run_search_example(mcp_service: MCPService):
    """Run a search example using the Brave Search MCP server."""
    # Get the MCP tools for the agent
    mcp_tools = mcp_service.get_tools_for_agent(["brave"])
    
    if not mcp_tools:
        logger.error("No tools discovered from the Brave Search MCP server.")
        return
        
    logger.info(f"Discovered {len(mcp_tools)} tools from the Brave Search MCP server.")
    
    # Create an agent with the MCP tools
    agent = Agent(
        name="Tyler",
        model_name="gpt-4o",
        tools=mcp_tools  # Only use MCP tools for this example
    )
    
    # Create a thread
    thread = Thread()
    
    # Add a user message
    thread.add_message(Message(
        role="user",
        content="I'm researching renewable energy technologies. Can you search for the latest "
                "developments in solar panel efficiency and summarize the key findings?"
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


async def run_comparison_example(mcp_service: MCPService):
    """Run a comparison example using both Brave Search and built-in web tools."""
    # Get the MCP tools for the agent
    mcp_tools = mcp_service.get_tools_for_agent(["brave"])
    
    if not mcp_tools:
        logger.error("No tools discovered from the Brave Search MCP server.")
        return
        
    logger.info(f"Discovered {len(mcp_tools)} tools from the Brave Search MCP server.")
    
    # Create an agent with both MCP tools and built-in web tools
    agent = Agent(
        name="Tyler",
        model_name="gpt-4o",
        tools=["web"] + mcp_tools  # Use both built-in web tools and MCP tools
    )
    
    # Create a thread
    thread = Thread()
    
    # Add a user message that encourages using both types of tools
    thread.add_message(Message(
        role="user",
        content="I'm interested in quantum computing. Can you search for information about "
                "recent quantum computing breakthroughs and provide a summary? "
                "Feel free to use both the brave search tools and the built-in web tools."
    ))
    
    # Process the thread
    logger.info("Processing thread...")
    processed_thread, new_messages = await agent.go(thread)
    
    # Print the assistant's response
    for message in new_messages:
        if message.role == "assistant":
            logger.info(f"Assistant: {message.content}")


async def main():
    """Run the example."""
    # Check for Brave API key
    brave_api_key = os.environ.get("BRAVE_API_KEY")
    if not brave_api_key:
        logger.warning("BRAVE_API_KEY environment variable not set. "
                      "Please set it to use the Brave Search API.")
        return
        
    logger.info("Initializing MCP service with Brave Search server...")
    
    # Configure the Brave Search MCP server
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
        }
    ]
    
    # Initialize the MCP service
    mcp_service = await initialize_mcp_service(server_configs)
    
    try:
        # Run the search example
        logger.info("\n\n=== Running Search Example ===\n")
        await run_search_example(mcp_service)
        
        # Run the comparison example
        logger.info("\n\n=== Running Comparison Example ===\n")
        await run_comparison_example(mcp_service)
                
    finally:
        # Clean up the MCP service
        logger.info("\nCleaning up MCP service...")
        await cleanup_mcp_service()


if __name__ == "__main__":
    asyncio.run(main()) 