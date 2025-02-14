---
sidebar_position: 3
---

# Message API

The `Message` class represents individual interactions within a thread. It handles text content, attachments, and metadata for each message in a conversation.

## Initialization

```python
from tyler.models.message import Message

# Basic message
message = Message(
    role="user",
    content="Hello!"
)

# Message with attachments
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
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | str | No | Auto-generated | Unique message identifier |
| `role` | str | Yes | None | Message role (system/user/assistant/tool) |
| `sequence` | int | No | None | Message sequence in thread |
| `content` | str or list | No | None | Message content (text or multimodal) |
| `name` | str | No | None | Tool name (for tool messages) |
| `tool_call_id` | str | No | None | Tool call ID (required for tool messages) |
| `tool_calls` | list | No | None | Tool calls (for assistant messages) |
| `attributes` | dict | No | Empty dict | Custom metadata |
| `timestamp` | datetime | No | Current UTC time | Message timestamp |
| `source` | dict | No | None | Source information |
| `attachments` | list | No | Empty list | File attachments |
| `metrics` | dict | No | Default metrics | Message metrics and analytics |

### Metrics Structure

```python
{
    "model": None,          # Model used for generation
    "timing": {
        "started_at": None,
        "ended_at": None,
        "latency": 0
    },
    "usage": {
        "completion_tokens": 0,
        "prompt_tokens": 0,
        "total_tokens": 0
    },
    "weave_call": {
        "id": "",
        "ui_url": ""
    }
}
```

## Methods

### model_dump

Convert message to a dictionary suitable for JSON serialization.

```python
def model_dump(self) -> Dict[str, Any]
```

Returns a complete dictionary representation of the message, including:
- All message fields
- Serialized attachments
- Metrics and analytics
- Tool calls (if any)

### to_chat_completion_message

Return message in the format expected by chat completion APIs.

```python
def to_chat_completion_message(self) -> Dict[str, Any]
```

Formats the message for LLM API calls, including:
- Proper role and content formatting
- Multimodal content support (text + images)
- Tool calls and responses
- Processed file contents

### ensure_attachments_stored

Ensure all attachments are stored if needed.

```python
async def ensure_attachments_stored(self, force: bool = False) -> None
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `force` | bool | No | False | Force storage even if already stored |

### add_attachment

Add an attachment to the message.

```python
def add_attachment(self, attachment: Union[Attachment, bytes], filename: Optional[str] = None) -> None
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `attachment` | Attachment or bytes | Yes | None | Either an Attachment object or raw bytes |
| `filename` | str | Only with bytes | None | Required when attachment is bytes |

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

## Message Content Types

Messages support both text and multimodal content:

```python
# Text message
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
                "url": "data:image/jpeg;base64,..."
            }
        }
    ]
)
```

## Working with Attachments

There are three ways to add attachments to a message:

### 1. During Message Creation

```python
# Add file during creation using file_content and filename
message = Message(
    role="user",
    content="Here's a document",
    file_content=pdf_bytes,  # Raw file bytes
    filename="document.pdf"  # Will be automatically converted to attachment
)
```

### 2. Using add_attachment Method (Recommended)

```python
# Add attachment using raw bytes
message.add_attachment(pdf_bytes, filename="document.pdf")

# Add attachment using Attachment object
attachment = Attachment(filename="data.json", content=json_bytes)
message.add_attachment(attachment)
```

### 3. Direct List Manipulation

```python
# Append a single attachment
attachment = Attachment(filename="data.json", content=json_bytes)
message.attachments.append(attachment)

# Add multiple attachments
message.attachments.extend([
    Attachment(filename="doc1.pdf", content=pdf1_bytes),
    Attachment(filename="doc2.pdf", content=pdf2_bytes)
])
```

### Attachment Processing

Attachments are automatically processed based on type:
- PDFs: Text extraction and overview
- Images: OCR, object detection, description
- JSON: Parsing and structure analysis

### Ensuring Storage

After adding attachments, you may need to ensure they are properly stored:

```python
# Store all attachments (if not already stored)
await message.ensure_attachments_stored()

# Force re-storage of all attachments
await message.ensure_attachments_stored(force=True)
```

## Best Practices

1. **Message Creation**
   ```python
   # Use appropriate roles
   user_msg = Message(role="user", content="Question")
   system_msg = Message(role="system", content="You are a helpful assistant")
   
   # Include source information
   slack_msg = Message(
       role="user",
       content="Hello",
       source={
           "name": "slack",
           "channel": "C123",
           "ts": "1234567890.123"
       }
   )
   ```

2. **File Handling**
   ```python
   # Add files with proper metadata
   message = Message(
       role="user",
       content="Please analyze this",
       file_content=pdf_bytes,
       filename="report.pdf"
   )
   
   # Ensure files are stored
   await message.ensure_attachments_stored()
   ```

3. **Tool Messages**
   ```python
   # Create tool message
   tool_msg = Message(
       role="tool",
       name="weather",
       content='{"temp": 72}',
       tool_call_id="call_123"
   )
   
   # Assistant with tool calls
   assistant_msg = Message(
       role="assistant",
       content="Let me check the weather",
       tool_calls=[{
           "id": "call_123",
           "type": "function",
           "function": {
               "name": "get_weather",
               "arguments": '{"location": "London"}'
           }
       }]
   )
   ```

4. **Metrics Tracking**
   ```python
   # Access message metrics
   print(f"Tokens used: {message.metrics['usage']['total_tokens']}")
   print(f"Latency: {message.metrics['timing']['latency']}ms")
   ```

## See Also

- [Agent API](./agent.md)
- [Thread API](./thread.md)
- [Attachment API](./attachment.md)
- [Examples](../examples/index.md)

See the [Attachment](attachment.md) documentation for more details. 