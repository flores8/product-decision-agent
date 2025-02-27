---
sidebar_position: 3
---

# Tools API

Tyler provides a set of built-in tools organized by functionality. Each tool follows the OpenAI function calling format and includes Weave monitoring integration.

## Web Tools

### web-fetch_page

Fetches content from a web page and returns it in a clean, readable format.

```python
{
    "name": "web-fetch_page",
    "parameters": {
        "url": str,          # Required: The URL to fetch
        "format": str,       # Optional: "text" or "html" (default: "text")
        "headers": dict      # Optional: Headers to send with the request
    }
}
```

Returns:
```python
{
    "success": bool,
    "status_code": int,
    "content": str,
    "content_type": str,
    "error": Optional[str]
}
```

### web-download_file

Downloads a file from a URL and saves it to the downloads directory.

```python
{
    "name": "web-download_file",
    "parameters": {
        "url": str,          # Required: The URL of the file to download
        "filename": str,     # Optional: Name to save the file as
        "headers": dict      # Optional: Headers to send with the request
    }
}
```

Returns:
```python
{
    "success": bool,
    "file_path": str,
    "content_type": str,
    "file_size": int,
    "filename": str,
    "error": Optional[str]
}
```

## File Tools

### read-file

Reads and extracts content from files, with special handling for PDFs and text files.

```python
{
    "name": "read-file",
    "parameters": {
        "file_url": str,     # Required: Path to the file
        "mime_type": str     # Optional: MIME type hint for processing
    }
}
```

Returns:
```python
{
    "text": str,            # Extracted text content
    "type": str,           # File type (e.g., "pdf", "text")
    "pages": int,          # For PDFs: number of pages
    "empty_pages": list,   # For PDFs: list of pages without text
    "processing_method": str,  # For PDFs: "text" or "vision"
    "file_url": str,
    "error": Optional[str]
}
```

## Image Tools

### image-generate

Generates images using DALL-E 3 based on text descriptions.

```python
{
    "name": "image-generate",
    "parameters": {
        "prompt": str,       # Required: Text description of desired image
        "size": str,        # Optional: "1024x1024", "1792x1024", or "1024x1792"
        "quality": str,     # Optional: "standard" or "hd"
        "style": str        # Optional: "vivid" or "natural"
    }
}
```

Returns:
```python
(
    {
        "success": bool,
        "description": str,
        "details": {
            "filename": str,
            "size": str,
            "quality": str,
            "style": str,
            "created": int
        }
    },
    [
        {
            "content": str,  # Base64 encoded image
            "filename": str,
            "mime_type": str,
            "description": str
        }
    ]
)
```

### analyze-image

Analyzes and describes image contents using GPT-4V.

```python
{
    "name": "analyze-image",
    "parameters": {
        "file_url": str,     # Required: Path to the image file
        "prompt": str        # Optional: Prompt to guide the analysis
    }
}
```

Returns:
```python
{
    "success": bool,
    "analysis": str,
    "file_url": str,
    "error": Optional[str]
}
```

## Audio Tools

### text-to-speech

Converts text to speech using AI voices.

```python
{
    "name": "text-to-speech",
    "parameters": {
        "input": str,        # Required: Text to convert (max 4096 chars)
        "voice": str,        # Optional: "alloy", "echo", "fable", "onyx", "nova", "shimmer"
        "model": str,        # Optional: "tts-1" or "tts-1-hd"
        "response_format": str,  # Optional: "mp3", "opus", "aac", "flac"
        "speed": float       # Optional: 0.25 to 4.0
    }
}
```

Returns:
```python
(
    {
        "success": bool,
        "description": str,
        "details": {
            "filename": str,
            "voice": str,
            "model": str,
            "format": str,
            "speed": float,
            "text_length": int
        }
    },
    [
        {
            "content": bytes,  # Audio content
            "filename": str,
            "mime_type": str,
            "description": str
        }
    ]
)
```

### speech-to-text

Transcribes speech from audio files to text.

```python
{
    "name": "speech-to-text",
    "parameters": {
        "file_url": str,     # Required: Path to the audio file
        "language": str,     # Optional: ISO-639-1 language code
        "prompt": str        # Optional: Guide for style/continuation
    }
}
```

Returns:
```python
{
    "success": bool,
    "text": str,
    "details": {
        "model": str,
        "language": str,
        "file_url": str
    },
    "error": Optional[str]
}
```

## Command Line Tools

### command_line-run_command

Executes whitelisted command line operations safely.

```python
{
    "name": "command_line-run_command",
    "parameters": {
        "command": str,      # Required: Command to execute
        "working_dir": str   # Optional: Working directory (default: ".")
    }
}
```

Supported Commands:
- Navigation & Read (unrestricted):
  - `ls`: List directory contents
  - `pwd`: Print working directory
  - `cd`: Change directory
  - `cat`: Display file contents
  - `find`: Search for files
  - `grep`: Search patterns in files
  - `tree`: Display directory structure
  - `wc`: Count lines/words/chars
  - `head/tail`: Show start/end of files
  - `diff`: Compare files

- File Operations (workspace only):
  - `mkdir`: Create directory
  - `touch`: Create empty file
  - `rm`: Remove file/empty dir
  - `cp`: Copy file
  - `mv`: Move/rename file
  - `echo`: Write to file
  - `sed`: Edit file content

Returns:
```python
{
    "command": str,
    "working_dir": str,
    "output": str,
    "error": Optional[str],
    "exit_code": int
}
```

## Using Tools

Tools can be used by passing their module names to the Agent constructor:

```python
from tyler.models.agent import Agent

# Use specific tool modules
agent = Agent(
    tools=["web", "files", "image", "audio", "command_line"]
)

# Mix with custom tools
agent = Agent(
    tools=[
        "web",
        custom_tool,
        "command_line"
    ]
)
```

## Custom Tools

Custom tools must follow this format:

```python
custom_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "custom_tool",
            "description": "Tool description",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter description"
                    }
                },
                "required": ["param1"]
            }
        }
    },
    "implementation": lambda param1: f"Result: {param1}",
    "attributes": {  # Optional
        "type": "interrupt"  # Only valid attribute
    }
}
```

## Error Handling

Tools should return structured responses:

```python
{
    "success": bool,         # Whether the operation succeeded
    "error": Optional[str],  # Error message if failed
    "result": Any           # Operation result if succeeded
}
```

## Monitoring

Tools use Weave for monitoring and tracing:

```python
@weave.op(name="custom-tool")
def monitored_tool(*, param1: str) -> Dict:
    try:
        result = process_param(param1)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

## See Also

- [Agent API](./agent.md)
- [Thread API](./thread.md)
- [Message API](./message.md)
- [Examples](../examples/tools.md) 