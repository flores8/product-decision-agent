# MCP Integration for Tyler

This module provides integration with the [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/mcp) for Tyler. It allows Tyler to connect to MCP servers, discover tools, and use them in conversations.

## Overview

The MCP integration consists of the following components:

- **MCPServerManager**: Manages the lifecycle of MCP servers (start/stop)
- **MCPService**: Connects to MCP servers, discovers tools, and converts them to Tyler's format
- **Utility functions**: Provides global access to the MCP service

## Usage

### Basic Usage

```python
import asyncio
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.mcp.utils import initialize_mcp_service, cleanup_mcp_service

async def main():
    # Configure MCP servers
    server_configs = [
        {
            "name": "brave",
            "transport": "stdio",
            "start_command": "python -m mcp.servers.brave_search",
            "env": {
                "BRAVE_API_KEY": "your-api-key"
            }
        }
    ]
    
    # Initialize the MCP service
    mcp_service = await initialize_mcp_service(server_configs)
    
    try:
        # Get MCP tools for the agent
        mcp_tools = mcp_service.get_tools_for_agent()
        
        # Create an agent with MCP tools
        agent = Agent(
            model_name="gpt-4o",
            tools=["web"] + mcp_tools
        )
        
        # Use the agent normally
        thread = Thread()
        thread.add_message(Message(role="user", content="Search for quantum computing breakthroughs"))
        processed_thread, new_messages = await agent.go(thread)
        
    finally:
        # Clean up
        await cleanup_mcp_service()

if __name__ == "__main__":
    asyncio.run(main())
```

### Server Configuration

Each MCP server configuration can include the following fields:

- `name` (required): A unique name for the server (used for namespacing tools)
- `transport`: The transport type to use (`stdio`, `sse`, or `websocket`)
- `start_command`: Command to start the server (for `stdio` transport)
- `url`: URL to connect to the server (for `sse` and `websocket` transports)
- `env`: Environment variables to pass to the server
- `headers`: HTTP headers to include in requests (for `sse` and `websocket` transports)
- `startup_timeout`: Time to wait for the server to start (in seconds)
- `required`: Whether the server is required (if `true`, failure to connect will be logged as an error)

### Tool Namespacing

Tools from MCP servers are namespaced with the server name to avoid conflicts:

```
{server_name}.{tool_name}
```

For example, a tool named `search` from a server named `brave` would be available as `brave.search`.

## Requirements

- Python 3.8+
- MCP Python SDK (`pip install mcp>=1.3.0`)

## Examples

See the `examples` directory for examples of using the MCP integration:

- `mcp_brave_search.py`: Example using the Brave Search MCP server
- `mcp_multi_server.py`: Example using multiple MCP servers 