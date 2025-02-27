# Tools Overview

Tyler comes with several built-in tool modules and supports custom tools to extend its capabilities. Each module can be enabled by including its name in the agent's `tools` configuration.

## Available Built-in Tools

- [Web Tools](./web.md) - Tools for interacting with web content
- [Slack Tools](./slack.md) - Tools for Slack workspace integration
- [Command Line Tools](./command-line.md) - Safe access to system commands
- [Notion Tools](./notion.md) - Tools for Notion workspace integration
- [Image Tools](./image.md) - Tools for image generation and manipulation
- [Audio Tools](./audio.md) - Tools for text-to-speech and speech-to-text conversion
- [File Tools](./files.md) - Tools for reading and processing various file types
- [Document Tools](./documents.md) - Tools for working with PDFs, CSVs, and JSON files

## Building Custom Tools

Tyler's functionality can be extended by creating custom tools. A custom tool consists of three main components:

1. **Function Definition**: OpenAI function schema describing the tool
2. **Implementation**: The actual Python function that executes the tool
3. **Attributes** (optional): Tool metadata - currently only supports `{"type": "interrupt"}` for interrupt tools

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

Tools can return files by using a tuple return format:

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
```

## Using Tools

### Basic Usage

To use both built-in and custom tools, include them in your agent's configuration:

```python
from tyler.models import Agent

# Define a custom tool
def calculator_implementation(operation: str, x: float, y: float) -> str:
    """Simple calculator implementation"""
    if operation == "add":
        result = x + y
    elif operation == "subtract":
        result = x - y
    elif operation == "multiply":
        result = x * y
    elif operation == "divide":
        result = x / y if y != 0 else "Error: division by zero"
    return f"Result: {result}"

custom_calculator = {
    "definition": {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform basic calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The mathematical operation to perform"
                    },
                    "x": {"type": "number", "description": "First number"},
                    "y": {"type": "number", "description": "Second number"}
                },
                "required": ["operation", "x", "y"]
            }
        }
    },
    "implementation": calculator_implementation
}

# Initialize agent with both built-in and custom tools
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with various tasks",
    tools=[
        "web",              # Built-in tools
        "slack",
        "notion",
        "command_line",
        "image",
        "audio",            # Audio processing tools
        "files",            # File handling tools
        "documents",        # Document processing tools
        custom_calculator   # Custom tool
    ]
)
```

### Tool Types

#### Standard Tools
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

#### Interrupt Tools
Interrupt tools can break the normal flow of tool execution:

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
            "error": f"Unexpected error: {str(e)}"
        }
```

## Environment Setup

Some tools require specific environment variables to be set. You can set these in your `.env` file:

```bash
# Slack Tools
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret

# Notion Tools
NOTION_API_KEY=your-api-key
NOTION_VERSION=2022-06-28

# Image Tools
OPENAI_API_KEY=your-openai-key

# Audio Tools
OPENAI_API_KEY=your-openai-key  # Required for text-to-speech and speech-to-text

# Document Tools
OPENAI_API_KEY=your-openai-key  # Required for PDF vision processing
```