---
sidebar_position: 4
---

# Core concepts

This guide explains the core concepts and components that make up Tyler's architecture.

## Agent

The `Agent` class is the central component of Tyler. It:
- Manages conversations through threads
- Processes messages using LLMs (with GPT-4o as default)
- Executes tools when needed
- Maintains conversation state
- Supports streaming responses
- Handles file attachments and processing
- Integrates with Weave for monitoring

### Basic usage

```python
from tyler.models.agent import Agent

agent = Agent(
    model_name="gpt-4o",
    temperature=0.7,
    purpose="To help with tasks",
    tools=["web", "slack", "notion"]
)

# Process a thread
result = await agent.go(thread)

# Process with streaming
async for update in agent.go_stream(thread):
    if update.type == StreamUpdate.Type.CONTENT_CHUNK:
        print(update.data, end="")
```

### Key methods

- `go(thread)`: Process a thread with tool execution
- `go_stream(thread)`: Process a thread with streaming updates
- `step(thread)`: Execute a single processing step
- `_process_message_files(message)`: Handle file attachments
- `_handle_tool_execution(tool_call)`: Execute tool calls

## Thread

Threads represent conversations and maintain:
- Message history
- System prompts
- Conversation metadata
- File attachments

### Creating threads

```python
from tyler.models.thread import Thread

# Basic thread
thread = Thread()

# Thread with system prompt
thread = Thread(
    system_prompt="You are a helpful assistant"
)

# Thread with attributes
thread = Thread(
    attributes={
        "source": "slack",
        "channel": "general"
    }
)
```

### Message handling

```python
# Add messages
thread.add_message(message)

# Get messages
messages = thread.messages

# Get last message
last = thread.get_last_message()

# Get messages by role
user_messages = thread.get_messages_by_role("user")
```

## Message

Messages are the basic units of conversation. They contain:
- Content (text)
- Role (user, assistant, system, tool)
- Attachments (files)
- Metadata

### Creating messages

```python
from tyler.models.message import Message

# Basic message
message = Message(
    role="user",
    content="Hello!"
)

# Message with attributes
message = Message(
    role="user",
    content="Hello!",
    attributes={
        "source": "slack",
        "user_id": "123"
    }
)

# Message with attachment
message = Message(
    role="user",
    content="Here's a file",
    attachments=[attachment]
)
```

## Attachment

Attachments handle files in conversations:
- Support multiple file types
- Automatic content extraction
- Secure storage
- Metadata tracking

### Creating attachments

```python
from tyler.models.attachment import Attachment

# From file path
attachment = Attachment.from_file("document.pdf")

# From bytes
attachment = Attachment(
    filename="image.png",
    content=image_bytes,
    mime_type="image/png"
)

# From URL
attachment = await Attachment.from_url("https://example.com/file.pdf")
```

## Tools

Tools extend agent capabilities:
- Web browsing
- File processing
- Service integration
- Custom functionality

### Built-in tools

```python
# Using built-in tools
agent = Agent(
    model_name="gpt-4o",
    tools=[
        "web",
        "slack",
        "notion"
    ]
)
```

### Custom tools

```python
# Define custom tool
weather_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
            }
        }
    },
    "implementation": lambda location: f"Weather in {location}: Sunny"
}

# Use custom tool
agent = Agent(
    model_name="gpt-4o",
    tools=[weather_tool]
)
```

## Storage

Tyler supports multiple storage backends:

### Thread storage

```python
# Memory storage (default)
from tyler.database.memory_store import MemoryThreadStore
store = MemoryThreadStore()

# PostgreSQL storage
from tyler.database.thread_store import ThreadStore
store = ThreadStore("postgresql://user:pass@localhost/db")

# Use with agent
agent = Agent(
    model_name="gpt-4o",
    thread_store=store
)
```

### File storage

```python
# Configure via environment
TYLER_FILE_STORAGE_TYPE=local
TYLER_FILE_STORAGE_PATH=/path/to/files

# Automatic handling
attachment = Attachment.from_file("document.pdf")
await attachment.ensure_stored()
```

## Streaming

Tyler supports streaming responses:

### Basic streaming

```python
async for update in agent.go_stream(thread):
    if update.type == StreamUpdate.Type.CONTENT_CHUNK:
        print(update.data, end="")
```

### Stream update types

- `CONTENT_CHUNK`: Partial content from assistant
- `ASSISTANT_MESSAGE`: Complete assistant message
- `TOOL_MESSAGE`: Tool execution result
- `COMPLETE`: Final thread state
- `ERROR`: Error during processing

## Error handling

Tyler provides robust error handling:

### Try-except blocks

```python
try:
    result = await agent.go(thread)
except Exception as e:
    print(f"Error: {str(e)}")
```

### Error messages

```python
# Error messages are added to thread
message = Message(
    role="assistant",
    content="Error: Tool execution failed",
    metrics={"error": str(e)}
)
thread.add_message(message)
```

## Next steps

- See [Examples](./category/examples) for practical usage
- Learn about [Configuration](./configuration.md)
- Explore [API reference](./category/api-reference) 