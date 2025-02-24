# Building Custom Tools

Tyler's functionality can be extended by creating custom tools. This guide explains how to build, test, and integrate your own tools.

## Tool Structure

A custom tool consists of three main components:

1. **Function Definition**: OpenAI function schema describing the tool
2. **Implementation**: The actual Python function that executes the tool
3. **Attributes** (optional): Tool metadata - currently only supports `{"type": "interrupt"}` for interrupt tools

## Creating a Custom Tool

### Basic Structure

```python
# custom_tools.py

TOOLS = [
    {
        "definition": {
            "type": "function",
            "function": {
                "name": "my-custom-tool",
                "description": "Description of what the tool does",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Description of parameter 1"
                        },
                        "param2": {
                            "type": "integer",
                            "description": "Description of parameter 2"
                        }
                    },
                    "required": ["param1"]
                }
            }
        },
        "implementation": my_tool_function,
        # Attributes are optional and only used for interrupt tools
        "attributes": {
            "type": "interrupt"  # Only valid attribute, used to mark interrupt tools
        }
    }
]
```

### Implementation Function

Your tool implementation can be either synchronous or asynchronous:

```python
# Synchronous implementation
def my_tool_function(param1: str, param2: int = 0) -> Union[str, Dict]:
    """
    Implement your tool logic here.
    Returns either a string or a dictionary with results.
    """
    result = do_something(param1, param2)
    return {
        "status": "success",
        "data": result
    }

# Asynchronous implementation
async def my_async_tool(param1: str, param2: int = 0) -> Union[str, Dict]:
    """
    Implement your async tool logic here.
    """
    result = await do_something_async(param1, param2)
    return {
        "status": "success",
        "data": result
    }
```

### Returning Files

Tools can return files by using a tuple return format. The tuple consists of two elements:
1. A dictionary containing the tool's response data
2. A list of file dictionaries (or None/empty list if no files)

```python
async def file_generating_tool() -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Tool that generates and returns files.
    
    Returns:
        Tuple containing:
            - Dict with response data (success status, messages, metadata etc.)
            - List of file dictionaries, each containing:
                - filename: Name of the file
                - content: File content as bytes
                - mime_type: MIME type of the file
                - description: Optional description of the file
    """
    # Generate your content
    content = generate_something()
    
    # Create file data
    file_data = {
        "filename": "output.txt",
        "content": content.encode('utf-8'),
        "mime_type": "text/plain",
        "description": "Generated output file"  # Optional
    }
    
    return (
        {
            "success": True, 
            "message": "File generated successfully",
            "metadata": {
                "file_count": 1,
                "total_size": len(content)
            }
        },
        [file_data]  # List of file dictionaries
    )

# Example of error case with no files
async def failing_tool() -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Tool that might fail to generate files."""
    try:
        # ... attempt to generate content ...
        raise Exception("Generation failed")
    except Exception as e:
        return (
            {
                "success": False,
                "error": str(e)
            },
            []  # Empty list for error case
        )
```

The tuple return format provides several benefits:
- Clear separation between tool response data and file attachments
- Consistent error handling with empty file list
- Support for multiple file attachments
- Ability to include metadata about the files
- Type safety with explicit return type annotation

When a tool returns files in this format, Tyler will automatically:
1. Process the response data as the tool's result
2. Convert the file dictionaries into proper attachments
3. Store the files in the configured storage backend
4. Attach the files to the tool's response message

## Tool Types

### Standard Tools

Most custom tools will be standard tools that perform specific actions:

```python
{
    "definition": {
        "type": "function",
        "function": {
            "name": "data-process",
            "description": "Process data in a specific format",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "Data to process"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["json", "csv", "xml"],
                        "description": "Data format"
                    }
                },
                "required": ["data", "format"]
            }
        }
    },
    "implementation": process_data
    # No attributes needed for standard tools
}
```

### Interrupt Tools

Interrupt tools can break the normal flow of tool execution. These are the only tools that use attributes:

```python
{
    "definition": {
        "type": "function",
        "function": {
            "name": "emergency-stop",
            "description": "Emergency stop for critical situations",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for emergency stop"
                    }
                },
                "required": ["reason"]
            }
        }
    },
    "implementation": emergency_stop,
    "attributes": {
        "type": "interrupt"  # Required for interrupt tools
    }
}
```

## Best Practices

### 1. Tool Naming

- Use descriptive, hyphenated names
- Include category prefix (e.g., "data-", "util-")
- Keep names concise but clear

### 2. Parameter Design

- Use clear parameter names
- Provide detailed descriptions
- Include type information
- Specify constraints
- Mark required parameters

### 3. Error Handling

```python
async def robust_tool(param: str) -> Dict:
    try:
        # Tool logic here
        result = await process(param)
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        return {
            "success": False,
            "error": f"Invalid input: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}"
        }
```

### 4. Documentation

- Provide clear descriptions
- Document parameters thoroughly
- Include usage examples
- Note any limitations
- Specify requirements

## Integration

### Local File

```python
# my_tools.py
from typing import Dict

def my_tool(param: str) -> Dict:
    return {"result": f"Processed {param}"}

TOOLS = [
    {
        "definition": {
            "type": "function",
            "function": {
                "name": "my-tool",
                "description": "Example tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param": {
                            "type": "string",
                            "description": "Input parameter"
                        }
                    },
                    "required": ["param"]
                }
            }
        },
        "implementation": my_tool
    }
]
```

### Configuration

```yaml
# tyler-config.yaml
tools:
  - "web"  # Built-in tools
  - "slack"
  - "./my_tools.py"  # Custom tools
```

Or programmatically:

```python
from tyler.models import Agent

agent = Agent(
    model_name="gpt-4o",
    tools=[
        "web",  # Built-in tools
        {  # Custom tool inline
            "definition": {...},
            "implementation": my_tool
        }
    ]
)
```

## Testing

### Unit Testing

```python
import pytest
from your_tools import my_tool

def test_my_tool():
    # Test successful execution
    result = my_tool("test input")
    assert result["success"] is True
    assert "data" in result
    
    # Test error handling
    result = my_tool("")
    assert result["success"] is False
    assert "error" in result

@pytest.mark.asyncio
async def test_async_tool():
    result = await my_async_tool("test input")
    assert result["success"] is True
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_tool_in_agent():
    agent = Agent(
        model_name="gpt-4o",
        tools=[{"definition": {...}, "implementation": my_tool}]
    )
    
    thread = Thread()
    message = Message(
        role="user",
        content="Use my-tool with parameter 'test'"
    )
    thread.add_message(message)
    
    processed_thread, new_messages = await agent.go(thread)
    assert any(m.role == "tool" for m in new_messages)
```

## Security Considerations

1. **Input Validation**
   - Validate all parameters
   - Sanitize inputs
   - Check file paths
   - Verify permissions

2. **Resource Management**
   - Implement timeouts
   - Handle rate limits
   - Monitor resource usage
   - Clean up temporary files

3. **Error Handling**
   - Catch all exceptions
   - Provide clear error messages
   - Log errors appropriately
   - Fail gracefully

4. **Data Security**
   - Protect sensitive data
   - Use secure storage
   - Implement access controls
   - Follow security best practices 