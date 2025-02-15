---
sidebar_position: 3
---

# Attachment API

The `Attachment` class represents files attached to messages in Tyler. It handles file content storage, processing, and retrieval, supporting both direct content storage and external file storage backends.

## Initialization

```python
from tyler.models.attachment import Attachment

attachment = Attachment(
    filename: str,
    content: Optional[Union[bytes, str]] = None,
    mime_type: Optional[str] = None,
    processed_content: Optional[Dict[str, Any]] = None,
    file_id: Optional[str] = None,
    storage_path: Optional[str] = None,
    storage_backend: Optional[str] = None,
    status: Literal["pending", "stored", "failed"] = "pending"
)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `filename` | str | Yes | - | Name of the attached file |
| `content` | Optional[Union[bytes, str]] | No | None | File content as bytes or base64 string |
| `mime_type` | Optional[str] | No | None | MIME type of the file |
| `processed_content` | Optional[Dict[str, Any]] | No | None | Processed version of the file content |
| `file_id` | Optional[str] | No | None | Reference ID in storage backend |
| `storage_path` | Optional[str] | No | None | Path in storage backend |
| `storage_backend` | Optional[str] | No | None | Type of storage backend used |
| `status` | Literal["pending", "stored", "failed"] | No | "pending" | Current status of the attachment |

## Methods

### model_dump

Convert attachment to a dictionary suitable for JSON serialization.

```python
def model_dump(self) -> Dict[str, Any]
```

#### Returns

| Type | Description |
|------|-------------|
| Dict[str, Any] | JSON-serializable dictionary of attachment data |

#### Example

```python
attachment = Attachment(filename="example.txt", content=b"Hello World")
data = attachment.model_dump()
```

### get_content_bytes

Get the content as bytes, converting from base64 if necessary.

```python
async def get_content_bytes(self) -> bytes
```

#### Returns

| Type | Description |
|------|-------------|
| bytes | File content as bytes |

#### Raises

| Exception | Description |
|-----------|-------------|
| ValueError | When no content is available |

#### Example

```python
content = await attachment.get_content_bytes()
```

### process

Process the attachment content using the file processor.

```python
async def process(self) -> None
```

#### Raises

| Exception | Description |
|-----------|-------------|
| Exception | If file processing fails |

#### Example

```python
await attachment.process()
processed_data = attachment.processed_content
```

### ensure_stored

Ensure the attachment is stored in the configured storage backend. Note: This is automatically called by ThreadStore when saving a thread - you typically don't need to call this directly.

```python
async def ensure_stored(self, force: bool = False) -> None
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `force` | bool | No | False | Force storage even if already stored |

#### Raises

| Exception | Description |
|-----------|-------------|
| RuntimeError | If attachment has no content or storage fails |

#### Example

```python
# Note: You typically don't need to call this directly
# as ThreadStore handles it automatically when saving a thread
await attachment.ensure_stored()

# Force re-store attachment if needed
await attachment.ensure_stored(force=True)
```

## Best Practices

1. **Content Handling**
   ```python
   # Binary content
   attachment = Attachment(
       filename="document.pdf",
       content=pdf_bytes,
       mime_type="application/pdf"
   )

   # Base64 content
   attachment = Attachment(
       filename="image.png",
       content=base64_string,
       mime_type="image/png"
   )
   ```

2. **Storage Management**
   ```python
   # Storage is handled automatically by ThreadStore
   # No need to call ensure_stored() directly
   thread.add_message(message_with_attachment)
   await thread_store.save(thread)  # This will store attachments automatically
   ```

3. **Content Retrieval**
   ```python
   # Get content safely
   try:
       content = await attachment.get_content_bytes()
   except ValueError as e:
       print(f"Content not available: {e}")
   ```

4. **Status Checking**
   ```python
   # Check attachment status
   if attachment.status == "stored":
       content = await attachment.get_content_bytes()
   elif attachment.status == "failed":
       print("Storage failed")
   else:
       await attachment.ensure_stored()
   ```

## See Also

- [Agent API](./agent.md)
- [Message API](./message.md)
- [File Storage Examples](../examples/file-storage.md)