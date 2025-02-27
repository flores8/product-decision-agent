---
sidebar_position: 3
---

# Message API

The `Message` class represents individual interactions within a thread. It handles text and multimodal content, attachments, metrics, and metadata for each message in a conversation.

## Initialization

```python
from tyler.models.message import Message
from datetime import datetime, UTC

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

# Message with file attachment
message = Message(
    role="assistant",
    content="Here's the analysis",
    file_content=pdf_bytes,  # Raw file bytes
    filename="document.pdf"  # Will be automatically converted to attachment
)

# Tool message
message = Message(
    role="tool",
    name="weather_tool",
    content='{"temperature": 72}',
    tool_call_id="call_123"  # Required for tool messages
)

# Message with source and attributes
message = Message(
    role="user",
    content="Hello!",
    source={"name": "slack", "thread_id": "123"},
    attributes={"customer_id": "456"}
)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | str | No | Auto-generated | Unique message identifier (SHA-256 hash of content) |
| `role` | Literal["system", "user", "assistant", "tool"] | Yes | None | Message role |
| `sequence` | Optional[int] | No | None | Message sequence in thread (0 for system, incremental for others) |
| `content` | Optional[Union[str, List[Union[TextContent, ImageContent]]]] | No | None | Message content (text or multimodal) |
| `name` | Optional[str] | No | None | Tool name (for tool messages) |
| `tool_call_id` | Optional[str] | No | None | Tool call ID (required for tool messages) |
| `tool_calls` | Optional[list] | No | None | Tool calls (for assistant messages) |
| `attributes` | Dict | No | {} | Custom metadata |
| `timestamp` | datetime | No | now(UTC) | Message timestamp |
| `source` | Optional[Dict[str, Any]] | No | None | Source information |
| `attachments` | List[Attachment] | No | [] | File attachments |
| `metrics` | Dict[str, Any] | No | Default metrics | Message metrics and analytics |

### Content Types

```python
# TypedDict definitions for content types
class ImageUrl(TypedDict):
    url: str

class ImageContent(TypedDict):
    type: Literal["image_url"]
    image_url: ImageUrl

class TextContent(TypedDict):
    type: Literal["text"]
    text: str
```

### Metrics Structure

```python
{
    "model": None,          # Model used for generation
    "timing": {
        "started_at": None, # Start timestamp
        "ended_at": None,   # End timestamp
        "latency": 0        # Processing time in seconds
    },
    "usage": {
        "completion_tokens": 0,
        "prompt_tokens": 0,
        "total_tokens": 0
    },
    "weave_call": {
        "id": "",          # Weave trace ID
        "ui_url": ""       # Weave UI URL
    }
}
```

## Methods

### model_dump

Convert message to a dictionary suitable for JSON serialization.

```python
def model_dump(self) -> Dict[str, Any]
```

Returns a complete dictionary representation including:
```python
{
    "id": str,
    "role": str,
    "sequence": int,
    "content": Union[str, List],
    "name": Optional[str],
    "tool_call_id": Optional[str],
    "tool_calls": Optional[List],
    "timestamp": str,        # ISO format with timezone
    "source": Optional[Dict],
    "metrics": Dict,
    "attachments": Optional[List[Dict]]  # Serialized attachments
}
```

### to_chat_completion_message

Return message in the format expected by chat completion APIs.

```python
def to_chat_completion_message(self) -> Dict[str, Any]
```

Returns:
```python
{
    "role": str,
    "content": str,
    "sequence": int,
    "name": Optional[str],        # For tool messages
    "tool_calls": Optional[List], # For assistant messages
    "tool_call_id": Optional[str] # For tool messages
}
```

For messages with attachments:
- User messages: Adds file references to content
- Assistant messages: Adds file metadata to content

### ensure_attachments_stored

Ensure all attachments are stored in the configured storage backend.

```python
async def ensure_attachments_stored(
    self,
    force: bool = False
) -> None
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `force` | bool | No | False | Force storage even if already stored |

Raises `RuntimeError` if storage fails.

### add_attachment

Add an attachment to the message.

```python
def add_attachment(
    self,
    attachment: Union[Attachment, bytes],
    filename: Optional[str] = None
) -> None
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `attachment` | Union[Attachment, bytes] | Yes | None | Attachment object or raw bytes |
| `filename` | Optional[str] | With bytes | None | Required when attachment is bytes |

#### Examples

```python
# Add using raw bytes
message.add_attachment(pdf_bytes, filename="document.pdf")

# Add using Attachment object
attachment = Attachment(filename="data.json", content=json_bytes)
message.add_attachment(attachment)
```

## Field Validators

### ensure_timezone

Ensures timestamp is timezone-aware UTC.

```python
@field_validator("timestamp", mode="before")
def ensure_timezone(cls, value: datetime) -> datetime
```

### validate_role

Validate role field.

```python
@field_validator("role")
def validate_role(cls, v: str) -> str
```

Ensures role is one of: system, user, assistant, tool

### validate_tool_message

Validate tool message requirements.

```python
@model_validator(mode='after')
def validate_tool_message(self) -> 'Message'
```

Ensures tool messages have required tool_call_id

### validate_tool_calls

Validate tool_calls field structure.

```python
@field_validator("tool_calls")
def validate_tool_calls(cls, v: list) -> list
```

Ensures tool calls have proper structure with id, type, and function fields

## Best Practices

1. **Message Sequencing**
   ```python
   # System messages get sequence 0
   system_msg = Message(role="system", content="System prompt")
   thread.add_message(system_msg)  # Gets sequence 0
   
   # Other messages get incremental sequences
   user_msg = Message(role="user", content="Hello")
   thread.add_message(user_msg)    # Gets sequence 1
   ```

2. **File Handling**
   ```python
   # Add file during creation
   message = Message(
       content="Here's a file",
       file_content=bytes_data,
       filename="data.pdf"
   )
   
   # Or add after creation
   message.add_attachment(bytes_data, filename="data.pdf")
   
   # Always store attachments
   await message.ensure_attachments_stored()
   ```

3. **Tool Messages**
   ```python
   # Tool messages require tool_call_id
   tool_msg = Message(
       role="tool",
       name="web_search",
       content="Search results...",
       tool_call_id="call_123"
   )
   ```

4. **Metrics Tracking**
   ```python
   # Update metrics after processing
   message.metrics.update({
       "model": "gpt-4o",
       "timing": {
           "started_at": start_time,
           "ended_at": end_time,
           "latency": latency
       },
       "usage": response.usage
   })
   ```

## See Also

- [Thread API](./thread.md)
- [Attachment API](./attachment.md)
- [Core Concepts](../core-concepts.md) 