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
- Message history with proper sequencing
- System prompts
- Conversation metadata and analytics
- Source tracking (e.g., Slack, web)
- Token usage statistics
- Performance metrics

### Creating threads

```python
from tyler.models.thread import Thread

# Basic thread
thread = Thread()

# Thread with title and source
thread = Thread(
    title="Support Conversation",
    source={
        "name": "slack",
        "channel": "C123",
        "thread_ts": "1234567890.123"
    }
)

# Thread with attributes
thread = Thread(
    attributes={
        "customer_id": "123",
        "priority": "high"
    }
)
```

### Message handling

```python
# Add messages (automatically handles sequencing)
system_msg = Message(role="system", content="You are a helpful assistant")
thread.add_message(system_msg)  # Gets sequence 0

user_msg = Message(role="user", content="Hello!")
thread.add_message(user_msg)    # Gets sequence 1

# Get messages by role
last_user = thread.get_last_message_by_role("user")
last_assistant = thread.get_last_message_by_role("assistant")

# Get messages for LLM completion
messages = thread.get_messages_for_chat_completion()
```

### Analytics and monitoring

```python
# Get token usage
stats = thread.get_total_tokens()
print(f"Total tokens: {stats['overall']['total_tokens']}")
print(f"By model: {stats['by_model']}")

# Get timing statistics
timing = thread.get_message_timing_stats()
print(f"Average latency: {timing['average_latency']}s")

# Get message distribution
counts = thread.get_message_counts()
print(f"Messages: {counts}")

# Get tool usage
tools = thread.get_tool_usage()
print(f"Tool calls: {tools['total_calls']}")
```

### Thread management

```python
# Generate descriptive title
title = await thread.generate_title()

# Ensure system prompt
thread.ensure_system_prompt("You are a helpful assistant")

# Clear conversation
thread.clear_messages()

# Convert to dict for storage
thread_data = thread.to_dict()
```

## Message

Messages are the basic units of conversation. They contain:
- Content (text or multimodal)
- Role (user, assistant, system, tool)
- Sequence number for ordering
- Attachments (files with automatic processing)
- Metrics (token usage, timing, model info)
- Source information
- Custom attributes

### Creating messages

```python
from tyler.models.message import Message

# Basic text message
message = Message(
    role="user",
    content="Hello!"
)

# Multimodal message (text + images)
message = Message(
    role="user",
    content=[
        {
            "type": "text",
            "text": "What's in this image?"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "path/to/image.jpg"
            }
        }
    ]
)

# Message with attributes and source
message = Message(
    role="user",
    content="Hello!",
    attributes={
        "customer_id": "123",
        "priority": "high"
    },
    source={
        "name": "slack",
        "thread_id": "123456"
    }
)

# Message with file attachment
message = Message(
    role="user",
    content="Here's a file",
    file_content=pdf_bytes,
    filename="document.pdf"
)

# Tool message
message = Message(
    role="tool",
    name="weather_tool",
    content='{"temperature": 72}',
    tool_call_id="call_123"  # Required for tool messages
)
```

### Message metrics

Messages automatically track various metrics:

```python
# Message metrics structure
message.metrics = {
    "model": "gpt-4o",          # Model used for generation
    "timing": {
        "started_at": "2024-02-26T12:00:00Z",
        "ended_at": "2024-02-26T12:00:01Z",
        "latency": 1.0
    },
    "usage": {
        "completion_tokens": 100,
        "prompt_tokens": 50,
        "total_tokens": 150
    },
    "weave_call": {
        "id": "call-123",
        "ui_url": "https://weave.ui/call-123"
    }
}
```

### Working with attachments

```python
# Add attachment using raw bytes
message.add_attachment(pdf_bytes, filename="document.pdf")

# Add attachment using Attachment object
attachment = Attachment(filename="data.json", content=json_bytes)
message.add_attachment(attachment)

# Ensure attachments are stored
await message.ensure_attachments_stored()
```

### Message serialization

```python
# Convert to chat completion format
chat_message = message.to_chat_completion_message()

# Convert to storage format
message_data = message.model_dump()
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