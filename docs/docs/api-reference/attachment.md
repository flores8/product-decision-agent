---
sidebar_position: 4
---

# Attachment API

The `Attachment` class represents files attached to messages in Tyler. It handles file content storage, processing, and retrieval, supporting both direct content storage and external file storage backends.

## Initialization

```python
from tyler.models.attachment import Attachment

# Basic attachment
attachment = Attachment(
    filename="document.pdf",
    content=pdf_bytes,
    mime_type="application/pdf"
)

# Attachment with processed content
attachment = Attachment(
    filename="image.png",
    content=image_bytes,
    mime_type="image/png",
    processed_content={
        "type": "image",
        "text": "OCR extracted text",
        "overview": "Image description",
        "url": "/files/images/image.png"
    }
)

# Attachment with storage info
attachment = Attachment(
    filename="data.json",
    file_id="file_123",
    storage_path="data/file_123.json",
    storage_backend="local",
    status="stored"
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

### Storage Status

| Status | Description |
|--------|-------------|
| `pending` | Initial state, not yet stored |
| `stored` | Successfully stored in backend |
| `failed` | Storage attempt failed |

## Methods

### model_dump

Convert attachment to a dictionary suitable for JSON serialization.

```python
def model_dump(self) -> Dict[str, Any]
```

Returns:
```python
{
    "filename": str,
    "mime_type": str,
    "processed_content": Optional[Dict],
    "file_id": Optional[str],
    "storage_path": Optional[str],
    "storage_backend": Optional[str],
    "status": str,
    "content": Optional[str]  # Base64 if no file_id
}
```

### get_content_bytes

Get the content as bytes, converting from base64 if necessary.

```python
async def get_content_bytes(self) -> bytes
```

Retrieves content from:
1. Storage backend if `file_id` exists
2. `content` field if stored as bytes
3. Decodes `content` if stored as base64 string

Raises `ValueError` if no content is available.

### update_processed_content_with_url

Update processed_content with URL after storage.

```python
def update_processed_content_with_url(self) -> None
```

Adds a URL to processed_content based on storage_path:
```python
{
    "url": f"/files/{storage_path}"
}
```

### ensure_stored

Ensure the attachment is stored in the configured storage backend.

```python
async def ensure_stored(
    self,
    force: bool = False
) -> None
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `force` | bool | No | False | Force storage even if already stored |

#### Storage Process
1. Checks if storage is needed
2. Converts content to bytes if needed
3. Saves to configured backend
4. Updates metadata (file_id, storage_path, etc.)
5. Updates status to "stored" or "failed"
6. Adds URL to processed_content

#### Example

```python
try:
    await attachment.ensure_stored()
    if attachment.status == "stored":
        print(f"Stored at: {attachment.storage_path}")
        print(f"URL: {attachment.processed_content['url']}")
except RuntimeError as e:
    print(f"Storage failed: {e}")
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
   # Let ThreadStore handle storage
   thread.add_message(message_with_attachment)
   await thread_store.save(thread)  # Stores attachments

   # Or store manually if needed
   if attachment.status == "pending":
       await attachment.ensure_stored()
   ```

3. **Content Retrieval**
   ```python
   # Get content safely
   try:
       content = await attachment.get_content_bytes()
   except ValueError as e:
       print(f"Content not available: {e}")
   ```

4. **Processed Content**
   ```python
   # Add processed content
   attachment.processed_content = {
       "type": "document",
       "text": extracted_text,
       "overview": summary
   }

   # Access processed content safely
   overview = attachment.processed_content.get("overview")
   text = attachment.processed_content.get("text")
   ```

5. **URL Access**
   ```python
   # Get public URL after storage
   if attachment.status == "stored":
       url = attachment.processed_content.get("url")
       if url:
           print(f"Access at: {url}")
   ```

## See Also

- [Message API](./message.md)
- [Thread API](./thread.md)
- [File Storage Examples](../examples/file-storage.md)