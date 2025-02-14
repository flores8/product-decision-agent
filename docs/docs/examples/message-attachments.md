---
sidebar_position: 7
---

# Message Attachments

This example demonstrates how to work with file attachments in Tyler messages, including adding files, automatic processing, and storage management.

## Overview

The example shows:
- Adding attachments to messages
- Automatic file processing
- Storage configuration
- Working with different file types
- Handling multiple attachments

## Code

```python
from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.models.attachment import Attachment
from tyler.storage import init_file_store
import asyncio
import os
import weave

# Load environment variables from .env file
load_dotenv()

# Initialize weave for tracing (optional)
if os.getenv("WANDB_API_KEY"):
    weave.init("tyler")

async def example_basic_attachment():
    """
    Demonstrates basic attachment functionality with different file types.
    """
    print("\n=== Basic Attachment Example ===")
    
    # Initialize file storage with custom path (optional)
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "files")
    init_file_store('local', base_path=data_dir)
    
    # Create agent
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help analyze documents"
    )
    
    # Create thread with PDF attachment
    thread = Thread()
    message = Message(role="user", content="Can you analyze these files?")
    
    # Add a PDF using add_attachment with bytes
    pdf_content = b"This is example PDF content for testing attachments."
    message.add_attachment(pdf_content, filename="document.pdf")
    
    # Add a text file using Attachment object
    text_attachment = Attachment(
        filename="notes.txt",
        content=b"Important meeting notes:\n1. Review project timeline\n2. Update documentation",
        mime_type="text/plain"
    )
    message.add_attachment(text_attachment)
    
    thread.add_message(message)
    
    # Process thread - files will be automatically stored and processed
    processed_thread, new_messages = await agent.go(thread)
    
    print("\nAssistant's response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)

async def example_multiple_attachments():
    """
    Demonstrates handling multiple attachments in a single message.
    """
    print("\n=== Multiple Attachments Example ===")
    
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help analyze multiple documents"
    )
    
    thread = Thread()
    message = Message(
        role="user",
        content="Please analyze these reports"
    )
    
    # Add multiple files using add_attachment
    files = [
        ("report.txt", b"Q1 sales increased by 15%"),
        ("data.json", b'{"customer_satisfaction": 4.5}'),
        ("notes.md", b"# Project Updates\n- Timeline on track\n- Budget approved")
    ]
    
    for filename, content in files:
        message.add_attachment(content, filename=filename)
    
    thread.add_message(message)
    
    # Process thread with multiple attachments
    processed_thread, new_messages = await agent.go(thread)
    
    print("\nAssistant's response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)

async def example_attachment_processing():
    """
    Demonstrates attachment processing and storage.
    """
    print("\n=== Attachment Processing Example ===")
    
    agent = Agent(model_name="gpt-4o")
    thread = Thread()
    
    # Create a message with an image attachment
    message = Message(
        role="user",
        content="What's in this image?"
    )
    
    # Add an image using add_attachment
    with open("example.jpg", "rb") as f:
        image_bytes = f.read()
    message.add_attachment(image_bytes, filename="example.jpg")
    
    thread.add_message(message)
    
    # Process thread - image will be automatically analyzed
    processed_thread, new_messages = await agent.go(thread)
    
    print("\nAssistant's response (with image analysis):")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)

async def main():
    # Run all examples
    await example_basic_attachment()
    await example_multiple_attachments()
    await example_attachment_processing()

if __name__ == "__main__":
    asyncio.run(main())
```

## Examples

### 1. Basic Attachment
```python
# Add attachment using bytes
message.add_attachment(pdf_bytes, filename="document.pdf")

# Add attachment using Attachment object
attachment = Attachment(
    filename="data.json",
    content=json_bytes,
    mime_type="application/json"
)
message.add_attachment(attachment)
```
Demonstrates:
- Adding single files
- Using different methods
- Basic processing

### 2. Multiple Attachments
```python
# Add multiple files
files = [
    ("report.txt", b"Report content"),
    ("data.json", b'{"data": "value"}')
]

for filename, content in files:
    message.add_attachment(content, filename=filename)
```
Shows how to:
- Add multiple files
- Process in sequence
- Maintain organization

### 3. Attachment Processing
```python
# Image attachment with automatic analysis
message.add_attachment(image_bytes, filename="photo.jpg")

# Ensure attachments are stored
await message.ensure_attachments_stored()
```
Features:
- Automatic processing
- Content extraction
- Image analysis
- Storage management

## Configuration

### Environment Variables
```bash
# File Storage Configuration
TYLER_FILE_STORAGE_TYPE=local  # or s3
TYLER_FILE_STORAGE_PATH=/path/to/files

# For S3 Storage
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-2
TYLER_S3_BUCKET=your-bucket-name
```

### Storage Types

#### Local Storage
```python
init_file_store('local', base_path='/path/to/files')
```

#### S3 Storage
```python
init_file_store('s3', 
    bucket_name='your-bucket',
    aws_access_key_id='your-key',
    aws_secret_access_key='your-secret'
)
```

## Key Concepts

1. **Attachment Methods**
   - Using add_attachment
   - Bytes vs Attachment objects
   - File organization
   - Storage management

2. **File Processing**
   - Content extraction
   - Type detection
   - Automatic handling
   - Error management

3. **Storage Structure**
   - File organization
   - Metadata tracking
   - Efficient storage
   - Scalable design

4. **File Types**
   - PDFs
   - Images
   - Text files
   - Binary data

## Best Practices

1. **Adding Attachments**
   ```python
   # Preferred: Use add_attachment
   message.add_attachment(file_bytes, filename="doc.pdf")
   
   # Alternative: Use Attachment object
   attachment = Attachment(filename="doc.pdf", content=file_bytes)
   message.add_attachment(attachment)
   ```

2. **File Handling**
   ```python
   # Ensure proper storage
   await message.ensure_attachments_stored()
   
   # Check attachment status
   for attachment in message.attachments:
       print(f"{attachment.filename}: {attachment.file_id}")
   ```

3. **Security**
   ```python
   # Validate file types
   if not filename.endswith(('.pdf', '.txt', '.jpg')):
       raise ValueError("Unsupported file type")
   
   # Check file size
   if len(file_content) > MAX_FILE_SIZE:
       raise ValueError("File too large")
   ```

4. **Performance**
   ```python
   # Process files efficiently
   for file in files:
       message.add_attachment(file.content, filename=file.name)
   
   # Store all at once
   await message.ensure_attachments_stored()
   ```

## See Also

- [Message API](../api-reference/message.md) - Message documentation
- [Attachment API](../api-reference/attachment.md) - Attachment details
- [Storage Configuration](../configuration.md#file-storage) - Storage setup

See the [Attachment API](../api-reference/attachment.md) documentation for more details. 