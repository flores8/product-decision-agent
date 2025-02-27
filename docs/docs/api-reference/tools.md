---
sidebar_position: 7
---

# Tools API

The Tyler tools system provides a flexible framework for extending agent capabilities through function-based tools. Tools can be built-in or custom, and are automatically executed by agents during conversations.

## Tool Structure

Each tool is defined by a dictionary with required components:

```python
tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": str,
            "description": str,
            "parameters": {
                "type": "object",
                "properties": Dict[str, Any],
                "required": List[str]
            }
        }
    },
    "implementation": Callable,
    "attributes": Optional[Dict]  # Tool metadata
}
```

### Tool Definition

The definition follows OpenAI's function calling format:

```python
definition = {
    "type": "function",
    "function": {
        "name": "tool-name",
        "description": "What the tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Parameter description"
                },
                "param2": {
                    "type": "integer",
                    "description": "Parameter description"
                }
            },
            "required": ["param1"]
        }
    }
}
```

### Tool Implementation

The implementation can be a simple function or a monitored operation:

```python
# Simple function
def implementation(param1: str, param2: int = 0) -> Any:
    return result

# Monitored function
@weave.op(name="tool-name")
def implementation(*, param1: str, param2: int = 0) -> Dict:
    return {
        "success": True,
        "result": result,
        "error": None
    }
```

### Tool Attributes

Optional attribute for interrupt behavior:

```python
attributes = {
    "type": "interrupt"  # Only valid attribute - indicates tool can interrupt processing
}
```

## Built-in Tools

### Web Tools

```python
from tyler.tools import WEB_TOOLS

# Available tools
web_fetch_page = {
    "name": "web-fetch_page",
    "description": "Fetch and parse web content",
    "parameters": {
        "url": str,
        "format": Literal["text", "html"]
    }
}

web_download_file = {
    "name": "web-download_file",
    "description": "Download files from URLs",
    "parameters": {
        "url": str,
        "filename": Optional[str]
    }
}
```

### File Tools

```python
from tyler.tools import FILES_TOOLS

# Available tools
file_read = {
    "name": "file-read",
    "description": "Read file contents",
    "parameters": {
        "path": str
    }
}

file_write = {
    "name": "file-write",
    "description": "Write content to file",
    "parameters": {
        "path": str,
        "content": Union[str, bytes]
    }
}
```

### Document Tools

```python
from tyler.tools import DOCUMENTS_TOOLS

# Available tools
parse_document = {
    "name": "document-parse",
    "description": "Extract text and structure from documents",
    "parameters": {
        "file_path": str,
        "format": str
    }
}
```

### Image Tools

```python
from tyler.tools import IMAGE_TOOLS

# Available tools
process_image = {
    "name": "image-process",
    "description": "Process and analyze images",
    "parameters": {
        "image_path": str,
        "operations": List[str]
    }
}
```

### Audio Tools

```python
from tyler.tools import AUDIO_TOOLS

# Available tools
transcribe_audio = {
    "name": "audio-transcribe",
    "description": "Convert speech to text",
    "parameters": {
        "audio_path": str,
        "language": Optional[str]
    }
}
```

### Integration Tools

```python
from tyler.tools import SLACK_TOOLS, NOTION_TOOLS

# Slack tools
post_message = {
    "name": "slack-post_message",
    "description": "Post message to Slack",
    "parameters": {
        "channel": str,
        "text": str
    }
}

# Notion tools
create_page = {
    "name": "notion-create_page",
    "description": "Create Notion page",
    "parameters": {
        "parent_id": str,
        "title": str,
        "content": str
    }
}
```

## Creating Custom Tools

Custom tools are defined as dictionaries and passed directly to the Agent constructor:

### Basic Tool

```python
custom_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "custom-tool",
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
    "implementation": lambda param1: f"Result: {param1}"
}

# Use with agent
agent = Agent(tools=[custom_tool])

# Mix with built-in tools
agent = Agent(tools=["web", custom_tool, "slack"])
```

### Monitored Tool

```python
@weave.op(name="custom-tool")
def implementation(*, param1: str) -> Dict:
    try:
        result = process(param1)
        return {
            "success": True,
            "result": result,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": str(e)
        }

monitored_tool = {
    "definition": {...},
    "implementation": implementation
}

# Use with agent
agent = Agent(tools=[monitored_tool])
```

### Tool with Dependencies

```python
def create_tool(api_key: str):
    async def implementation(param1: str):
        client = ApiClient(api_key)
        return await client.process(param1)
    
    return {
        "definition": {...},
        "implementation": implementation,
        "attributes": {
            "type": "interrupt"
        }
    }

# Create tool instance and use with agent
tool = create_tool(os.environ["API_KEY"])
agent = Agent(tools=[tool])
```

## Error Handling

Tools should handle errors gracefully:

```python
def robust_tool(param1: str) -> Dict:
    try:
        # Main logic
        result = process(param1)
        return {
            "success": True,
            "result": result,
            "error": None
        }
    except ValueError as e:
        # Input validation errors
        return {
            "success": False,
            "error": f"Invalid input: {e}"
        }
    except ConnectionError as e:
        # Network errors
        return {
            "success": False,
            "error": f"Connection failed: {e}"
        }
    except Exception as e:
        # Unexpected errors
        return {
            "success": False,
            "error": f"Tool failed: {e}"
        }
```

## Best Practices

1. **Clear Documentation**
   ```python
   tool = {
       "definition": {
           "function": {
               "description": "Detailed purpose and usage",
               "parameters": {
                   "properties": {
                       "param1": {
                           "description": "Clear parameter purpose and format"
                       }
                   }
               }
           }
       }
   }
   ```

2. **Structured Responses**
   ```python
   {
       "success": bool,      # Operation status
       "result": Any,        # Operation result
       "error": str,         # Error message
       "metadata": Dict      # Additional info
   }
   ```

3. **Input Validation**
   ```python
   def implementation(param1: str) -> Dict:
       if not param1:
           return {
               "success": False,
               "error": "param1 is required"
           }
       if len(param1) > 100:
           return {
               "success": False,
               "error": "param1 too long"
           }
   ```

4. **Resource Cleanup**
   ```python
   async def implementation(param1: str) -> Dict:
       client = None
       try:
           client = await connect()
           return {"success": True, "result": await client.process(param1)}
       finally:
           if client:
               await client.close()
   ```

5. **Rate Limiting**
   ```python
   from tyler.utils.rate_limit import rate_limit

   @rate_limit(calls=60, period=60)
   def implementation(param1: str) -> Dict:
       return process(param1)
   ```

## See Also

- [Agent API](./agent.md)
- [Thread API](./thread.md)
- [Message API](./message.md)
- [Examples](../examples/tools.md) 