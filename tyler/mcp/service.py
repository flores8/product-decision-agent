"""MCP service implementation for Tyler."""

import asyncio
import logging
import os
import signal
import subprocess
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Tuple, Protocol

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

# Try to import websocket_client, but don't fail if it's not available
try:
    from mcp.client.websocket import websocket_client
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("mcp.client.websocket module not available. WebSocket transport will not be supported.")

from ..utils.tool_runner import tool_runner

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Manages MCP server processes."""
    
    def __init__(self):
        self.processes = {}  # name -> subprocess.Popen
        self.server_configs = {}  # name -> config
        
    async def start_server(self, name: str, config: Dict[str, Any]) -> bool:
        """Start an MCP server if it has command and args configuration.
        
        Args:
            name: The name of the server
            config: Server configuration dictionary
            
        Returns:
            bool: True if server started successfully or was already running
        """
        if name in self.processes and self.processes[name].poll() is None:
            logger.info(f"MCP server {name} is already running")
            return True
            
        # Check for command and args format
        command = config.get("command")
        args = config.get("args", [])
        
        # If command is not provided, assume external management
        if not command:
            logger.info(f"No command for MCP server {name}, assuming external management")
            return False
        
        try:
            # Combine command and args
            cmd_to_run = f"{command} {' '.join(str(arg) for arg in args)}"
            logger.info(f"Starting MCP server {name}: {cmd_to_run}")
            
            # Get environment variables
            env_vars = config.get("env", {})
            # Merge with current environment
            process_env = os.environ.copy()
            process_env.update(env_vars)
            
            # Start the process
            process = subprocess.Popen(
                cmd_to_run,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                env=process_env,
                bufsize=1,  # Line buffered
                universal_newlines=True,  # Ensure text mode for pipes
                preexec_fn=os.setsid  # Use process group for clean termination
            )
            
            self.processes[name] = process
            self.server_configs[name] = config
            
            # Wait for server to start
            startup_timeout = config.get("startup_timeout", 5)
            await asyncio.sleep(startup_timeout)
            
            # Check if process is still running
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"MCP server {name} failed to start: {stderr}")
                logger.debug(f"MCP server {name} stdout: {stdout}")
                return False
                
            logger.info(f"MCP server {name} started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting MCP server {name}: {e}")
            return False
            
    async def stop_server(self, name: str) -> bool:
        """Stop an MCP server if it was started by this manager.
        
        Args:
            name: The name of the server to stop
            
        Returns:
            bool: True if server stopped successfully or was already stopped
        """
        if name not in self.processes:
            logger.info(f"MCP server {name} not managed by this instance")
            return False
            
        process = self.processes[name]
        if process.poll() is not None:
            logger.info(f"MCP server {name} is already stopped")
            return True
            
        try:
            logger.info(f"Stopping MCP server {name}")
            
            # Try graceful termination first
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            # Wait for process to terminate
            try:
                await asyncio.to_thread(process.wait, timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not terminated
                logger.warning(f"MCP server {name} did not terminate gracefully, force killing")
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                
            logger.info(f"MCP server {name} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping MCP server {name}: {e}")
            return False
            
    async def stop_all_servers(self) -> None:
        """Stop all MCP servers managed by this instance."""
        for name in list(self.processes.keys()):
            await self.stop_server(name)


class MCPService:
    """Service for managing MCP server connections and tool discovery."""
    
    def __init__(self):
        self.server_manager = MCPServerManager()
        self.sessions = {}  # server_name -> ClientSession
        self.exit_stacks = {}  # server_name -> AsyncExitStack
        self.discovered_tools = {}  # server_name -> {tool_name -> tyler_tool}
        
    async def initialize(self, server_configs: List[Dict[str, Any]]) -> None:
        """Initialize the MCP service with the provided server configurations.
        
        This method starts servers that have command and args configuration,
        connects to them, and discovers available tools.
        
        Args:
            server_configs: List of server configuration dictionaries
        """
        # Start servers that have command and args
        for config in server_configs:
            name = config.get("name")
            if not name:
                logger.error("Server configuration must include a name")
                continue
                
            # Start the server if it has command and args
            server_started = False
            if config.get("command") and "args" in config:
                server_started = await self.server_manager.start_server(name, config)
                
                if not server_started and config.get("required", False):
                    logger.error(f"Failed to start required MCP server {name}")
                    continue
                    
            # Connect to the server
            session = await self._connect_to_server(name, config)
            
            if session:
                # Discover tools from the server
                await self._discover_tools(name, session)
            elif config.get("required", False):
                logger.error(f"Failed to connect to required MCP server {name}")
                
                # If we started the server but couldn't connect, stop it
                if server_started:
                    logger.info(f"Stopping MCP server {name} due to connection failure")
                    await self.server_manager.stop_server(name)
            
    async def _connect_to_server(self, name: str, config: Dict[str, Any]) -> Optional[ClientSession]:
        """Connect to an MCP server using the provided configuration.
        
        Args:
            name: The name of the server
            config: Server configuration dictionary
            
        Returns:
            Optional[ClientSession]: The MCP client session if connection successful
        """
        try:
            # Create exit stack for resource management
            exit_stack = AsyncExitStack()
            self.exit_stacks[name] = exit_stack
            
            # Get transport configuration
            transport_type = config.get("transport", "sse")
            
            if transport_type == "stdio":
                # Get the process from server manager if it was started
                process = self.server_manager.processes.get(name)
                
                # For stdio transport, we need to connect to the already running process
                if process and process.poll() is None:
                    logger.info(f"Connecting to existing MCP server process for {name}")
                    
                    # Get the command from the server config
                    command = self.server_manager.server_configs[name].get("command", "")
                    args = self.server_manager.server_configs[name].get("args", [])
                    
                    # Get environment variables from the server config
                    env_vars = self.server_manager.server_configs[name].get("env", {})
                    # Merge with current environment
                    process_env = os.environ.copy()
                    process_env.update(env_vars)
                    
                    # Create StdioServerParameters with the actual command
                    server_params = StdioServerParameters(
                        command=command,  # Use the actual command from config
                        args=args,        # Use the actual args from config
                        env=process_env   # Pass the environment variables
                    )
                    
                    try:
                        # Use the stdio_client function to connect to the process
                        # This returns a tuple of (read_stream, write_stream)
                        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
                        read_stream, write_stream = stdio_transport
                        
                        # Create a session with these streams
                        session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
                        
                        # Initialize the session
                        await session.initialize()
                        self.sessions[name] = session
                        return session
                    except Exception as e:
                        logger.error(f"Failed to initialize MCP session for server {name}: {e}")
                        return None
                else:
                    logger.error(f"Process for server {name} not found or not running")
                    return None
                
            elif transport_type == "sse":
                # Get the URL for SSE transport
                url = config.get("url")
                if not url:
                    logger.error(f"url is required for sse transport for server {name}")
                    return None
                    
                # Connect to the server using SSE transport
                read_stream, write_stream = await exit_stack.enter_async_context(sse_client(url))
                session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
                
                # Initialize the session
                await session.initialize()
                return session
                
            elif transport_type == "websocket" and WEBSOCKET_AVAILABLE:
                # Get the URL for WebSocket transport
                url = config.get("url")
                if not url:
                    logger.error(f"url is required for websocket transport for server {name}")
                    return None
                    
                # Connect to the server using WebSocket transport
                read_stream, write_stream = await exit_stack.enter_async_context(websocket_client(url))
                session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
                
                # Initialize the session
                await session.initialize()
                return session
                
            else:
                if transport_type == "websocket" and not WEBSOCKET_AVAILABLE:
                    logger.error(f"WebSocket transport requested for server {name} but websocket module not available")
                else:
                    logger.error(f"Unsupported transport type {transport_type} for server {name}")
                return None
                
        except Exception as e:
            logger.error(f"Error connecting to MCP server {name}: {e}")
            return None
            
    async def _discover_tools(self, name: str, session: ClientSession) -> None:
        """Discover tools from an MCP server and convert to Tyler format.
        
        Args:
            name: The name of the server
            session: The MCP client session
        """
        try:
            # Get available tools
            response = await session.list_tools()
            tools = response.tools
            
            logger.info(f"Discovered {len(tools)} tools from MCP server {name}")
            
            # Convert to Tyler tool format
            self.discovered_tools[name] = {}
            for tool in tools:
                tyler_tool = self._convert_mcp_tool_to_tyler_tool(name, tool, session)
                self.discovered_tools[name][tool.name] = tyler_tool
                
                # Register the tool with Tyler's tool runner
                tool_name = tyler_tool["definition"]["function"]["name"]
                tool_runner.register_tool(
                    name=tool_name,
                    implementation=tyler_tool["implementation"],
                    definition=tyler_tool["definition"]["function"]
                )
                
                # Register tool attributes
                tool_runner.register_tool_attributes(tool_name, tyler_tool["attributes"])
                
        except Exception as e:
            logger.error(f"Failed to discover tools from MCP server {name}: {e}")
            
    def _convert_mcp_tool_to_tyler_tool(self, server_name: str, tool, session: ClientSession) -> Dict:
        """Convert an MCP tool definition to a Tyler tool definition.
        
        Args:
            server_name: The name of the server
            tool: The MCP tool object
            session: The MCP client session
            
        Returns:
            Dict: Tyler tool definition
        """
        # Create namespaced tool name
        namespaced_name = f"{server_name}.{tool.name}"
        
        # Create Tyler tool definition
        tyler_tool = {
            "definition": {
                "type": "function",
                "function": {
                    "name": namespaced_name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            },
            "implementation": self._create_tool_implementation(server_name, tool.name),
            "attributes": {
                "source": "mcp",
                "server": server_name,
                "original_name": tool.name
            }
        }
        
        return tyler_tool
        
    def _create_tool_implementation(self, server_name: str, tool_name: str):
        """Create a function that calls the MCP tool.
        
        Args:
            server_name: The name of the server
            tool_name: The name of the tool
            
        Returns:
            Callable: Async function that calls the MCP tool
        """
        async def call_mcp_tool(**kwargs):
            try:
                session = self.sessions.get(server_name)
                if not session:
                    raise ValueError(f"MCP client for server {server_name} not found")
                    
                # Call the tool
                result = await session.call_tool(tool_name, kwargs)
                return result.content
            except Exception as e:
                raise ValueError(f"Error calling MCP tool {server_name}.{tool_name}: {e}")
                
        return call_mcp_tool
        
    def get_tools_for_agent(self, server_names=None):
        """Get tools for specified servers or all servers if none specified.
        
        Args:
            server_names: Optional list of server names to get tools from
            
        Returns:
            List[Dict]: List of Tyler tool definitions
        """
        tools = []
        for server_name, server_tools in self.discovered_tools.items():
            if server_names is None or server_name in server_names:
                tools.extend(list(server_tools.values()))
        return tools
        
    async def cleanup(self):
        """Disconnect from all MCP servers and stop managed servers."""
        # Close exit stacks (which will disconnect sessions)
        for name, exit_stack in self.exit_stacks.items():
            try:
                await exit_stack.aclose()
            except Exception as e:
                logger.error(f"Error closing MCP client for {name}: {e}")
                
        # Stop managed servers
        await self.server_manager.stop_all_servers() 