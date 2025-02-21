---
sidebar_position: 4
---

# Chat with Tyler

There are two ways to interact with Tyler: through the web interface or using the command-line interface (CLI).

## Web Interface

A beautiful web interface for interacting with Tyler agents, providing real-time chat capabilities, file handling, and a modern UI.

![Tyler Chat UI Demo](/img/tyler_chat_UI_demo_short.gif)

### Features

#### Modern Interface
- **Beautiful Design**: Clean, responsive interface built with React and Material-UI
- **Dark Mode**: Support for light and dark themes
- **Mobile Friendly**: Works seamlessly on all devices

#### Real-time Interaction
- **WebSocket Communication**: Instant updates and responses
- **Message Threading**: Organized conversations with context
- **File Attachments**: Easy upload and processing of files
- **Message History**: Browse and preserve past conversations

#### Robust Architecture
- **FastAPI Backend**: High-performance server with WebSocket support
- **PostgreSQL Storage**: Persistent storage for messages and files
- **Redux State Management**: Clean and predictable state handling
- **API Documentation**: Auto-generated OpenAPI docs

### Try It Out

The complete source code is available on GitHub: [tyler-chat](https://github.com/adamwdraper/tyler-chat)

The repository includes:
- Frontend React application
- Backend FastAPI server
- Docker configuration for easy setup
- Comprehensive documentation

## Command Line Interface

For users who prefer terminal-based interactions, Tyler provides a powerful CLI that supports multiple conversation threads, tool integration, and customizable configuration. The CLI is included with the main Tyler package.

### Installation

The CLI is automatically installed when you install Tyler:

```bash
pip install tyler-agent
```

This provides the `tyler-chat` command.

### Quick Start

Start a new chat session:
```bash
tyler-chat
```

With a specific thread title:
```bash
tyler-chat --title "My Project Discussion"
```

Using a custom configuration file:
```bash
tyler-chat --config path/to/config.yaml
```

### Configuration

The CLI can be configured using a YAML file located in any of these locations (checked in order):

1. Explicitly provided path using `--config` option
2. `./tyler-chat-config.yaml` in the current directory
3. `~/.tyler/chat-config.yaml` in user's home directory
4. `/etc/tyler/chat-config.yaml` for system-wide configuration

Example configuration:
```yaml
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
tools:
  - "web"           # Web search and browsing capabilities
  - "slack"         # Slack integration tools
  - "notion"        # Notion integration tools
  - "command_line"  # System command execution tools
  - "./my_tools.py" # Custom tools from local file
```

### Available Commands

During a CLI chat session, you can use these commands:

- `/help` - Show help information
- `/new [title]` - Create a new thread with optional title
- `/threads` - List all available threads
- `/switch <id|number>` - Switch to a different thread using ID or number
- `/clear` - Clear the screen
- `/quit` or `/exit` - End the chat session

### Thread Management

Threads are numbered starting from 1 (oldest) in the `/threads` list. You can switch between threads using either:
- The thread number: `/switch 1` (switches to the oldest thread)
- The thread ID: `/switch abc123` (switches to thread with ID 'abc123')

### Custom Tools

You can extend Tyler's capabilities by creating custom tools. Create a Python file with a `TOOLS` list:

```python
# my_tools.py
TOOLS = [
    {
        "definition": {
            "name": "my_tool",
            "description": "Description of what the tool does",
            "parameters": {
                # Parameter definitions
            }
        },
        "implementation": lambda **kwargs: "Tool result"
    }
]
```

Add the path to your custom tools file in the configuration YAML to make it available during chat sessions.

### Environment Variables

Both the web interface and CLI respect environment variables defined in a `.env` file in your working directory. This is particularly useful for storing API keys and other sensitive configuration values.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).

For commercial use, please contact the author.