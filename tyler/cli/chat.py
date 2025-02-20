"""Command line interface for Tyler chat"""
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import os
import click
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
import json
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.live import Live
from rich.layout import Layout
from rich.table import Table
from rich import box
import yaml
from datetime import datetime
import weave
import importlib.util
import sys

from tyler.models.agent import Agent, StreamUpdate
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.database.memory_store import MemoryThreadStore

# Initialize rich console
console = Console()

class ChatManager:
    def __init__(self):
        self.agent = None
        self.current_thread = None
        self.thread_store = MemoryThreadStore()
        weave.init("tyler-cli")  # Initialize Weave
        
    def initialize_agent(self, config: Dict[str, Any] = None) -> None:
        """Initialize the agent with optional configuration"""
        if config is None:
            config = {}
        
        # Create agent with provided config
        self.agent = Agent(**config)
        
    async def create_thread(self, 
                          title: Optional[str] = None,
                          attributes: Optional[Dict] = None,
                          source: Optional[Dict] = None) -> Thread:
        """Create a new thread"""
        thread = Thread(
            title=title or "New Thread",
            attributes=attributes or {},
            source=source
        )
        await self.thread_store.save(thread)
        self.current_thread = thread
        return thread
        
    async def list_threads(self) -> list:
        """List all threads"""
        return await self.thread_store.list()
        
    async def switch_thread(self, thread_id: str) -> Optional[Thread]:
        """Switch to a different thread"""
        thread = await self.thread_store.get(thread_id)
        if thread:
            self.current_thread = thread
        return thread

    def format_message(self, message: Message) -> Panel:
        """Format a message for display"""
        if message.role == "system":
            return  # Don't display system messages
            
        # Determine style based on role
        style_map = {
            "user": "green",
            "assistant": "blue",
            "tool": "yellow"
        }
        style = style_map.get(message.role, "white")
        
        # Format content
        if message.role == "tool":
            # For tool messages, show a compact version
            title = f"[{style}]Tool Result: {message.name}[/]"
            content = message.content[:500] + "..." if len(message.content) > 500 else message.content
        elif message.role == "assistant" and message.tool_calls:
            # For assistant messages with tool calls, show both content and tools
            title = f"[{style}]Agent[/]"
            content = message.content if message.content else ""
            for tool_call in message.tool_calls:
                tool_name = tool_call["function"]["name"]
                args = json.dumps(json.loads(tool_call["function"]["arguments"]), indent=2)
                content += f"\n\n[yellow]Using tool: {tool_name}[/]\n{args}"
        else:
            title = f"[{style}]{'Agent' if message.role == 'assistant' else message.role.title()}[/]"
            content = message.content
            
        return Panel(
            Markdown(content) if content else "",
            title=title,
            border_style=style,
            box=box.ROUNDED
        )

    async def process_command(self, command: str) -> bool:
        """Process a command and return whether to continue the session"""
        cmd_parts = command.split()
        cmd = cmd_parts[0].lower()
        args = cmd_parts[1:]
        
        if cmd == "/help":
            self.show_help()
        elif cmd == "/new":
            title = " ".join(args) if args else None
            await self.create_thread(title=title)
            console.print(f"Created new thread: {self.current_thread.title}")
        elif cmd == "/quit" or cmd == "/exit":
            return False
        elif cmd == "/threads":
            threads = await self.list_threads()
            table = Table(title="Available Threads")
            table.add_column("ID")
            table.add_column("Title")
            table.add_column("Messages")
            table.add_column("Last Updated")
            
            for thread in threads:
                table.add_row(
                    thread.id,
                    thread.title,
                    str(len(thread.messages)),
                    thread.updated_at.strftime("%Y-%m-%d %H:%M:%S")
                )
            console.print(table)
        elif cmd == "/switch":
            if not args:
                console.print("[red]Error: Thread ID required[/]")
                return True
            thread = await self.switch_thread(args[0])
            if thread:
                console.print(f"Switched to thread: {thread.title}")
                # Display thread history
                for message in thread.messages:
                    panel = self.format_message(message)
                    if panel:
                        console.print(panel)
            else:
                console.print("[red]Error: Thread not found[/]")
        elif cmd == "/clear":
            console.clear()
        else:
            console.print(f"[red]Unknown command: {cmd}[/]")
            
        return True

    def show_help(self):
        """Show help information"""
        help_text = """
Available Commands:
/help     - Show this help message
/new      - Create a new thread
/threads  - List all threads
/switch   - Switch to a different thread
/clear    - Clear the screen
/quit     - Exit the chat
"""
        console.print(Panel(help_text, title="Help", border_style="blue"))

async def handle_stream_update(update: StreamUpdate, chat_manager: ChatManager):
    """Handle streaming updates from the agent"""
    if update.type == StreamUpdate.Type.CONTENT_CHUNK:
        console.print(update.data, end="")
    elif update.type == StreamUpdate.Type.ASSISTANT_MESSAGE:
        # Only print a new line and tool calls if present
        if update.data.tool_calls:
            console.print()  # New line after content chunks
            panel = chat_manager.format_message(update.data)
            if panel:
                console.print(panel)
    elif update.type == StreamUpdate.Type.TOOL_MESSAGE:
        panel = chat_manager.format_message(update.data)
        if panel:
            console.print(panel)
    elif update.type == StreamUpdate.Type.ERROR:
        console.print(f"[red]Error: {update.data}[/]")

def load_custom_tool(file_path: str) -> list:
    """Load custom tools from a Python file.
    
    The file should contain a TOOLS list that contains tool definitions.
    Each tool should be a dict with 'definition' and 'implementation' keys.
    """
    try:
        # Get the module name from the file name
        module_name = Path(file_path).stem
        
        # Load the module from the file path
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            raise ImportError(f"Could not load spec for {file_path}")
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Get the TOOLS list from the module
        if not hasattr(module, 'TOOLS'):
            raise AttributeError(f"Module {module_name} must define a TOOLS list")
            
        return module.TOOLS
    except Exception as e:
        console.print(f"[red]Error loading custom tools from {file_path}: {str(e)}[/]")
        return []

def load_config(config_file: Optional[str]) -> Dict[str, Any]:
    """Load configuration from file.
    
    Looks for config in the following locations (in order):
    1. Explicitly provided config file path (--config option)
    2. ./tyler-chat-config.yaml in current directory
    3. ~/.tyler/chat-config.yaml in user's home directory
    4. /etc/tyler/chat-config.yaml for system-wide config
    """
    if config_file:
        config_path = Path(config_file)
    else:
        # Check standard locations
        possible_locations = [
            Path.cwd() / "tyler-chat-config.yaml",  # Current directory
            Path.home() / ".tyler" / "chat-config.yaml",  # User's home directory
            Path("/etc/tyler/chat-config.yaml"),  # System-wide
        ]
        
        for loc in possible_locations:
            if loc.exists():
                config_path = loc
                break
        else:
            # No config found, create template in current directory
            template_path = Path.cwd() / "tyler-chat-config.yaml"
            if not template_path.exists():
                template = """# Tyler Chat Configuration
# Save this file as tyler-chat-config.yaml in:
#   - Current directory
#   - ~/.tyler/chat-config.yaml
#   - /etc/tyler/chat-config.yaml
# Or specify location with: tyler-chat --config path/to/config.yaml

# Agent Identity
name: "Tyler"
purpose: "To be a helpful AI assistant with access to various tools and capabilities."
notes: |
  - Prefer clear, concise communication
  - Use tools when appropriate to enhance responses
  - Maintain context across conversations

# Model Configuration
model_name: "gpt-4o"
temperature: 0.7
max_tool_iterations: 10

# Tool Configuration
# List of tools to load. Can be:
#   - Built-in tool module names (e.g., "web", "slack")
#   - Paths to Python files containing custom tools:
#     - "./my_tools.py"          # Relative to config file
#     - "~/tools/translate.py"    # User's home directory
#     - "/opt/tools/search.py"    # Absolute path
tools:
  - "web"           # Web search and browsing capabilities
  - "slack"         # Slack integration tools
  - "notion"        # Notion integration tools
  - "command_line"  # System command execution tools
  # - "./my_tools.py"  # Example custom tools (uncomment to use)
"""
                template_path.write_text(template)
                console.print(f"[yellow]Created template config at: {template_path}[/]")
            return {}
            
    try:
        with open(config_path) as f:
            if config_path.suffix in ['.yaml', '.yml']:
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
                
        # Process tools list to load custom tools
        if 'tools' in config and isinstance(config['tools'], list):
            processed_tools = []
            config_dir = config_path.parent
            
            for tool in config['tools']:
                if isinstance(tool, str):
                    if any(c in tool for c in ['/', '.py', '~']):  # Looks like a path
                        # Handle relative paths
                        if tool.startswith('./') or tool.startswith('../'):
                            tool_path = str(config_dir / tool)
                        # Handle home directory
                        elif tool.startswith('~'):
                            tool_path = str(Path(tool).expanduser())
                        else:
                            tool_path = tool
                            
                        # Load custom tools from the file
                        custom_tools = load_custom_tool(tool_path)
                        processed_tools.extend(custom_tools)
                    else:
                        # It's a built-in tool module name
                        processed_tools.append(tool)
                else:
                    # Non-string items (like dicts) pass through unchanged
                    processed_tools.append(tool)
                    
            config['tools'] = processed_tools
                    
        return config
    except Exception as e:
        console.print(f"[yellow]Warning: Error loading config from {config_path}: {str(e)}[/]")
        return {}

@click.command()
@click.option('--config', '-c', help='Path to config file (YAML or JSON)')
@click.option('--title', '-t', help='Initial thread title')
def main(config: Optional[str], title: Optional[str]):
    """Tyler Chat CLI"""
    try:
        # Load configuration
        config_data = load_config(config)
        
        # Initialize chat manager
        chat_manager = ChatManager()
        chat_manager.initialize_agent(config_data)
        
        # Create initial thread
        asyncio.run(chat_manager.create_thread(title=title))
        
        console.print("[bold blue]Welcome to Tyler Chat![/]")
        console.print("Type your message or /help for commands")
        
        # Main chat loop
        while True:
            # Get user input
            user_input = Prompt.ask("\nYou")
            
            # Check if it's a command
            if user_input.startswith('/'):
                should_continue = asyncio.run(chat_manager.process_command(user_input))
                if not should_continue:
                    break
                continue
            
            # Add user message to thread
            chat_manager.current_thread.add_message(Message(role="user", content=user_input))
            
            # Process with agent
            async def process_message():
                async for update in chat_manager.agent.go_stream(chat_manager.current_thread):
                    await handle_stream_update(update, chat_manager)
            
            asyncio.run(process_message())
            
    except KeyboardInterrupt:
        console.print("\nGoodbye!")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/]")
        raise

if __name__ == "__main__":
    main() 