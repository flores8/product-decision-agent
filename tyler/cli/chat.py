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
        
    def initialize_agent(self, config: Dict[str, Any] = None) -> None:
        """Initialize the agent with optional configuration"""
        if config is None:
            config = {}
        
        # Create agent with streaming enabled and any provided config
        config['stream'] = True  # Always enable streaming for better UX
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
            title = f"[{style}]Assistant[/]"
            content = message.content if message.content else ""
            for tool_call in message.tool_calls:
                tool_name = tool_call["function"]["name"]
                args = json.dumps(json.loads(tool_call["function"]["arguments"]), indent=2)
                content += f"\n\n[yellow]Using tool: {tool_name}[/]\n{args}"
        else:
            title = f"[{style}]{message.role.title()}[/]"
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

def load_config(config_file: Optional[str]) -> Dict[str, Any]:
    """Load configuration from file"""
    if not config_file:
        return {}
        
    config_path = Path(config_file)
    if not config_path.exists():
        console.print(f"[yellow]Warning: Config file not found: {config_file}[/]")
        return {}
        
    try:
        with open(config_path) as f:
            if config_path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
    except Exception as e:
        console.print(f"[red]Error loading config: {str(e)}[/]")
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