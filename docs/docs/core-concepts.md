---
sidebar_position: 4
---

# Core Concepts

Tyler is built around several core concepts that work together to create a powerful and flexible AI agent framework. Understanding these concepts is crucial for effectively using and extending Tyler.

See the [Examples](./category/examples.md) section for practical demonstrations and the [API Reference](./category/api-reference.md) for detailed documentation.

## Architecture Overview

Tyler's architecture is designed to be modular, extensible, and efficient:

```mermaid
graph TD
    A[Agent] --> B[Thread]
    B --> C[Messages]
    C --> D[Attachments]
    A --> E[Tools]
    A --> F[Storage]
    F --> G[Thread Store]
    F --> H[File Store]
    A --> I[Monitoring]
```

## Core Components

### Agent

The Agent is the central component that manages conversations and executes tasks:

```python
from tyler.models.agent import Agent

agent = Agent(
    model_name="gpt-4o",
    temperature=0.7,
    name="Tyler",
    purpose="To help with tasks",
    notes="",
    tools=["web", "command_line"],  # Built-in tool modules or custom tools
    max_tool_iterations=10
)
```

Key features:
- Manages conversation flow and tool execution
- Supports both built-in and custom tools
- Handles file processing and attachments
- Tracks performance metrics and token usage
- Supports async operations with weave tracing
- Configurable model and temperature settings
- Customizable system prompts and behavior

### Thread

Threads organize conversations and maintain context:

```python
from tyler.models.thread import Thread
from datetime import datetime, UTC

thread = Thread(
    id="thread-123",  # Auto-generated if not provided
    title="Example Thread",
    messages=[],
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
    attributes={},
    source={"name": "slack", "thread_id": "1234567890.123"}
)
```

Key features:
- Maintains ordered message history with sequence tracking
- Supports system prompts and ensures they're first
- Handles message attachments and file processing
- Tracks token usage and model metrics
- Supports custom attributes and source tracking
- Provides analytics and tool usage statistics
- Integrates with persistent storage

### Messages

Messages represent individual interactions within a thread:

```python
from tyler.models.message import Message
from datetime import datetime, UTC

message = Message(
    role="user",  # system, user, assistant, or tool
    content="What can you help me with?",
    sequence=1,  # Auto-managed by Thread
    attachments=[],
    name=None,  # Required for tool messages
    tool_call_id=None,  # Required for tool messages
    tool_calls=None,  # For assistant messages with tool calls
    attributes={},
    timestamp=datetime.now(UTC),
    source=None,
    metrics={
        "model": "gpt-4o",
        "timing": {
            "started_at": "2024-02-07T00:00:00+00:00",
            "ended_at": "2024-02-07T00:00:01+00:00",
            "latency": 1000
        },
        "usage": {
            "completion_tokens": 100,
            "prompt_tokens": 50,
            "total_tokens": 150
        }
    }
)
```

Key features:
- Supports multiple roles (system, user, assistant, tool)
- Handles file attachments with automatic processing
- Tracks message sequence and timestamps
- Maintains tool call information and results
- Stores performance metrics and token usage
- Supports multimodal content (text and images)
- Provides chat completion message formatting

### Attachments

Attachments handle files and media in conversations:

```python
from tyler.models.attachment import Attachment

attachment = Attachment(
    filename="document.pdf",
    content=b"raw file content",  # bytes or base64 string
    mime_type="application/pdf",
    processed_content=None,  # Will be populated after processing
    file_id=None,  # Set after storage
    storage_path=None,  # Set after storage
    storage_backend=None,  # Set after storage
    status="pending"  # pending, stored, or failed
)
```

Key features:
- Automatic content type detection
- Secure file storage with unique IDs
- Content processing based on file type
- Support for multiple storage backends
- Automatic base64 encoding/decoding
- File validation and size limits
- Tracks storage status and metadata

### Tools

Tools extend the agent's capabilities:

```python
# Standard tool definition
standard_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather",
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
    "implementation": get_weather_function,
    "attributes": {
        "type": "standard"  # or "interrupt" for special handling
    }
}

# Built-in tool modules
tools = ["web", "command_line", "notion"]  # Available modules
```

Key features:
- OpenAI function calling format
- Built-in tool modules for common tasks
- Support for custom tool implementations
- Tool attributes for special behaviors
- Automatic schema validation
- Error handling and metrics tracking
- Interrupt tools for flow control

## Data Flow

### Conversation Flow

1. User sends message
2. Message added to thread with attachments processed
3. Agent processes thread:
   - Ensures system prompt exists
   - Processes any file attachments
   - Gets completion from LLM
   - Automatically handles any tool calls
   - Tracks metrics and performance
4. New messages added to thread
5. Thread saved to storage

```python
# Example conversation flow
async def conversation():
    thread = Thread()
    
    # User message with attachment
    user_msg = Message(
        role="user", 
        content="Can you analyze this document?",
        attachments=[Attachment(filename="doc.pdf", content=pdf_bytes)]
    )
    thread.add_message(user_msg)
    
    # Process thread - handles everything automatically
    processed_thread, new_messages = await agent.go(thread)
    
    # Handle response
    for msg in new_messages:
        if msg.role == "assistant":
            print(f"Assistant: {msg.content}")
```

## Storage and Persistence

### Thread Store

Tyler supports persistent thread storage through SQLAlchemy:

```python
from tyler.database.thread_store import ThreadStore

# PostgreSQL for production
store = ThreadStore("postgresql+asyncpg://user:pass@localhost/dbname")

# SQLite for development
store = ThreadStore("sqlite+aiosqlite:///path/to/db.sqlite")

# In-memory for testing
store = ThreadStore(":memory:")

# Initialize database
await store.initialize()

# Save thread
thread = Thread()
await store.save(thread)

# Retrieve thread
thread = await store.get(thread.id)

# List recent threads
threads = await store.list_recent(limit=30)

# Find threads by attributes
threads = await store.find_by_attributes({"source": "slack"})
```

Key features:
- Async SQLAlchemy-based storage
- Support for PostgreSQL and SQLite
- Automatic schema management
- Thread and message persistence
- Efficient message ordering
- Attachment handling
- Pagination and search

### File Store

Secure file storage for attachments is automatically configured through environment variables:

```python
# File storage configuration in .env
TYLER_FILE_STORAGE_TYPE="local"  # Default storage type
TYLER_FILE_STORAGE_PATH="~/.tyler/files"  # Default storage path
TYLER_MAX_FILE_SIZE=52428800  # Optional, 50MB default
TYLER_MAX_STORAGE_SIZE=5368709120  # Optional, 5GB limit
TYLER_ALLOWED_MIME_TYPES=application/pdf,image/jpeg,image/png  # Optional, comma-separated list

# Files are automatically stored when added as attachments
message = Message(
    role="user",
    content="Here's the document",
    attachments=[
        Attachment(filename="doc.pdf", content=pdf_bytes)
    ]
)

# Files can be retrieved through attachments
for attachment in message.attachments:
    content = await attachment.get_content_bytes()
```

Key features:
- Zero-configuration setup with sensible defaults
- Environment-based configuration for all aspects:
  - Storage type and location
  - File size limits (50MB default)
  - Total storage limits (5GB default)
  - Allowed MIME types
- Secure file storage with validation
- MIME type detection and filtering
- Sharded directory structure
- Automatic cleanup of orphaned files
- Storage metrics and health checks

Supported file types:
```python
ALLOWED_MIME_TYPES = {
    # Documents
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'text/csv',
    'application/json',
    # Images
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/svg+xml',
    # Archives
    'application/zip',
    'application/x-tar',
    'application/gzip'
}
```

## Monitoring and Metrics

Tyler provides comprehensive monitoring through weave:

```python
# Metrics tracked per message
metrics = {
    "model": "gpt-4o",
    "timing": {
        "started_at": "2024-02-07T00:00:00+00:00",
        "ended_at": "2024-02-07T00:00:01+00:00",
        "latency": 1000  # milliseconds
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

# Thread-level analytics
token_usage = thread.get_total_tokens()
model_usage = thread.get_model_usage()
timing_stats = thread.get_message_timing_stats()
tool_usage = thread.get_tool_usage()
message_counts = thread.get_message_counts()
```

Key metrics:
- Token usage by model
- Response latency
- Tool execution time
- Message counts by role
- Tool usage statistics
- Storage utilization
- Error rates

## Error Handling

Tyler implements comprehensive error handling:

```python
try:
    result = await agent.go(thread)
except Exception as e:
    if "Failed to store attachment" in str(e):
        # Handle attachment storage failure
        pass
    elif "Database error" in str(e):
        # Handle database errors
        pass
    elif isinstance(e, FileStoreError):
        if isinstance(e, FileNotFoundError):
            # Handle missing file
            pass
        elif isinstance(e, StorageFullError):
            # Handle storage capacity exceeded
            pass
        elif isinstance(e, UnsupportedFileTypeError):
            # Handle invalid file type
            pass
        elif isinstance(e, FileTooLargeError):
            # Handle file size exceeded
            pass
    else:
        # Handle other errors
        pass
```

Error categories:
- Storage errors (file and database)
- Tool execution errors
- Model API errors
- Validation errors
- Rate limiting
- Authentication failures
- Network issues

## Best Practices

1. **Thread Management**
   - Keep threads focused on single topics
   - Use appropriate system prompts
   - Save threads after modifications
   - Clean up old threads regularly
   - Handle attachments properly

2. **Tool Design**
   - Follow OpenAI function format
   - Implement proper error handling
   - Use interrupt tools sparingly
   - Document tool behavior
   - Track tool metrics

3. **Storage**
   - Use PostgreSQL for production
   - Set appropriate file limits
   - Monitor storage usage
   - Handle cleanup properly
   - Validate file types

4. **Performance**
   - Monitor token usage
   - Track response times
   - Use appropriate models
   - Implement caching
   - Handle rate limits

5. **Security**
   - Validate all inputs
   - Secure file storage
   - Handle API keys properly
   - Implement rate limiting
   - Monitor usage patterns

## Next Steps

- Explore the [API Reference](./category/api-reference.md)
- Try the [Examples](./category/examples.md)
- Read the [Configuration Guide](./configuration.md) 