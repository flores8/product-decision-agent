# File operations

The files module provides tools for reading and processing various file types, with automatic content extraction.

## Available tools

### Read-file

Reads and extracts content from files with automatic format detection and processing.

#### Parameters

- `file_url` (string, required)
  - URL or path to the file
  - Must be a valid local file path

- `mime_type` (string, optional)
  - Optional MIME type hint for file processing
  - If not provided, will be auto-detected

#### Returns

A dictionary containing:
- `text`: Extracted text content (for text files)
- `type`: File type detected
- `file_url`: Original file path
- `mime_type`: Detected MIME type
- `error`: Error message if failed

For PDFs, additional fields:
- `pages`: Number of pages
- `empty_pages`: List of pages with no text
- `processing_method`: Method used ("text" or "vision")

## Example usage

```python
from tyler.models import Agent, Thread, Message

# Create an agent with file tools
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with file processing",
    tools=["files"]
)

# Create a thread to read a file
thread = Thread()
message = Message(
    role="user",
    content="Please read and extract the content from document.pdf"
)
thread.add_message(message)

# Process the thread - agent will use read-file tool
processed_thread, new_messages = await agent.go(thread)
```

## Best practices

1. **File Access**
   - Ensure file permissions are correct
   - Use absolute paths when possible
   - Verify file existence before processing
   - Handle large files appropriately

2. **Content Processing**
   - Let MIME type be auto-detected when possible
   - Handle text encoding properly
   - Consider file size limitations
   - Process files in chunks if needed

3. **Error Handling**
   - Check file existence
   - Handle permission issues
   - Manage encoding errors
   - Process format-specific errors

4. **Security**
   - Validate file paths
   - Check file permissions
   - Scan for malicious content
   - Limit file sizes

## Common use cases

1. **Document Processing**
   - Reading text files
   - Extracting PDF content
   - Processing configuration files
   - Analyzing log files

2. **Content Extraction**
   - Text extraction
   - Document parsing
   - Data extraction
   - Format conversion

3. **File Analysis**
   - Format detection
   - Content validation
   - Structure analysis
   - Encoding detection

## Limitations

1. **File Support**
   - Limited to supported formats
   - PDF processing may require OCR
   - Binary files not supported
   - Size limitations apply

2. **Processing Constraints**
   - Memory usage for large files
   - Processing time for complex files
   - OCR accuracy varies
   - Encoding detection limits

## Error handling

Common errors and solutions:

1. **File Access**
   - Check file existence
   - Verify permissions
   - Validate paths
   - Handle timeouts

2. **Processing Errors**
   - Handle corrupt files
   - Manage encoding issues
   - Process format errors
   - Handle extraction failures

3. **Resource Issues**
   - Monitor memory usage
   - Handle timeout errors
   - Manage concurrent access
   - Control file handles 