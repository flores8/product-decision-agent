# Tools Overview

Tyler comes with several built-in tool modules that provide various capabilities out of the box. Each module can be enabled by including its name in the agent's `tools` configuration.

## Available Built-in Tools

- [Web Tools](./web.md) - Tools for interacting with web content
- [Slack Tools](./slack.md) - Tools for Slack workspace integration
- [Command Line Tools](./command-line.md) - Safe access to system commands
- [Notion Tools](./notion.md) - Tools for Notion workspace integration
- [Image Tools](./image.md) - Tools for image generation and manipulation

## Custom Tools

You can create your own custom tools to extend Tyler's capabilities. See the [Custom Tools Guide](./custom-tools.md) for detailed instructions on building and integrating your own tools.

## Using Tools

To use these tools, include their module names in your agent's configuration:

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
        custom_calculator   # Custom tool
    ]
)
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
```