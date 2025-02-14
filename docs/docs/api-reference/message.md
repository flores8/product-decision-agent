---
sidebar_position: 3
---

# Message API

The `Message` class represents individual interactions within a thread. It handles text content, attachments, and metadata for each message in a conversation.

## Initialization

```python
from tyler.models.message import Message

message = Message(
    id: str = None,
    role: str = "user",
    content: str = None,
    attachments: List[Attachment] = None,
    attributes: Dict = None,
    created_at: datetime = None,
    updated_at: datetime = None
)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | str | No | None | Unique message identifier |
| `role` | str | No | "user" | Message role (user/assistant/system/tool) |
| `content` | str | No | None | Message text content |
| `attachments` | List[Attachment] | No | None | File attachments |
| `attributes` | Dict | No | None | Custom metadata |
| `created_at` | datetime | No | None | Creation timestamp |
| `updated_at` | datetime | No | None | Last update timestamp |

## Methods

### add_attachment

Add a file attachment to the message.

```python
def add_attachment(
    self,
    attachment: Attachment
) -> None
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `attachment` | Attachment | Yes | File attachment |

#### Example

```python
attachment = Attachment(file_path="document.pdf")
message.add_attachment(attachment)
```

### get_attachments

Get all attachments or filter by type.

```python
def get_attachments(
    self,
    content_type: str = None
) -> List[Attachment]
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `content_type` | str | No | None | Filter by MIME type |

#### Returns

| Type | Description |
|------|-------------|
| List[Attachment] | List of attachments |

#### Example

```python
# Get all attachments
attachments = message.get_attachments()

# Get only PDF attachments
pdfs = message.get_attachments(content_type="application/pdf")
```

### set_attribute

Set a custom attribute.

```python
def set_attribute(
    self,
    key: str,
    value: Any
) -> None
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | str | Yes | Attribute key |
| `value` | Any | Yes | Attribute value |

#### Example

```python
message.set_attribute("source", "email")
```

### get_attribute

Get a custom attribute.

```python
def get_attribute(
    self,
    key: str,
    default: Any = None
) -> Any
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | str | Yes | Attribute key |
| `default` | Any | No | Default value |

#### Returns

| Type | Description |
|------|-------------|
| Any | Attribute value or default |

#### Example

```python
source = message.get_attribute("source", default="unknown")
```

### update_content

Update the message content.

```python
def update_content(
    self,
    content: str
) -> None
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | str | Yes | New message content |

#### Example

```python
message.update_content("Updated message text")
```

## Properties

### id

Get the message identifier.

```python
@property
def id(self) -> str:
    return self._id
```

### role

Get the message role.

```python
@property
def role(self) -> str:
    return self._role
```

### content

Get the message content.

```python
@property
def content(self) -> str:
    return self._content
```

### attachments

Get all attachments.

```python
@property
def attachments(self) -> List[Attachment]:
    return self._attachments
```

### attributes

Get all custom attributes.

```python
@property
def attributes(self) -> Dict:
    return self._attributes
```

### created_at

Get creation timestamp.

```python
@property
def created_at(self) -> datetime:
    return self._created_at
```

### updated_at

Get last update timestamp.

```python
@property
def updated_at(self) -> datetime:
    return self._updated_at
```

## Message Roles

Messages can have different roles:

```python
# User message
user_msg = Message(
    role="user",
    content="What's the weather?"
)

# Assistant message
assistant_msg = Message(
    role="assistant",
    content="The weather is sunny."
)

# System message
system_msg = Message(
    role="system",
    content="You are a weather assistant."
)

# Tool message
tool_msg = Message(
    role="tool",
    content='{"temperature": 72, "condition": "sunny"}'
)
```

## Working with Attachments

### Adding Files

```python
# Add a PDF file
pdf = Attachment(file_path="document.pdf")
message.add_attachment(pdf)

# Add an image
image = Attachment(file_path="image.jpg")
message.add_attachment(image)

# Add multiple files
message = Message(
    content="Here are the files",
    attachments=[pdf, image]
)
```

### Processing Attachments

```python
# Get text content from PDFs
pdfs = message.get_attachments(content_type="application/pdf")
for pdf in pdfs:
    text = pdf.extract_text()
    
# Process images
images = message.get_attachments(content_type="image/jpeg")
for image in images:
    data = image.process_image()
```

## Events

The Message class emits events that can be subscribed to:

```python
from tyler.events import EventEmitter

def on_content_updated(event):
    print(f"Content updated: {event.content}")

message.events.on("content_updated", on_content_updated)
```

Available events:
- `content_updated`: Emitted when content changes
- `attachment_added`: Emitted when attachment is added
- `attribute_changed`: Emitted when attribute changes

## Best Practices

1. **Content Management**
   ```python
   # Use appropriate roles
   message = Message(
       role="user",
       content="Question"
   )
   
   # Update content safely
   message.update_content("New content")
   ```

2. **Attachment Handling**
   ```python
   # Check file size
   if attachment.size > MAX_SIZE:
       raise ValueError("File too large")
   
   # Process files appropriately
   if attachment.content_type == "application/pdf":
       text = attachment.extract_text()
   ```

3. **Attributes**
   ```python
   # Track message metadata
   message.set_attribute("client_id", "123")
   message.set_attribute("timestamp", datetime.now())
   
   # Access safely
   client = message.get_attribute("client_id", "unknown")
   ```

4. **Performance**
   ```python
   # Lazy load attachments
   attachment = Attachment(
       file_path="large_file.pdf",
       lazy_load=True
   )
   
   # Process when needed
   if need_content:
       content = attachment.get_content()
   ```

## See Also

- [Agent API](./agent.md)
- [Thread API](./thread.md)
- [Attachment API](./attachment.md)
- [Examples](../examples/index.md) 