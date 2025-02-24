# Tools Overview

Tyler comes with several built-in tool modules that provide various capabilities out of the box. Each module can be enabled by including its name in the agent's `tools` configuration.

## Available Tool Modules

- [Web Tools](./web.md) - Tools for interacting with web content
- [Slack Tools](./slack.md) - Tools for Slack workspace integration
- [Command Line Tools](./command-line.md) - Safe access to system commands
- [Notion Tools](./notion.md) - Tools for Notion workspace integration
- [Image Tools](./image.md) - Tools for image generation and manipulation

## Using Tools

To use these tools, include their module names in your agent's configuration:

```yaml
tools:
  - "web"           # Web tools
  - "slack"         # Slack tools
  - "notion"        # Notion tools
  - "command_line"  # Command line tools
  - "image"         # Image generation tools
```

Or when creating an agent programmatically:

```python
from tyler.models import Agent

agent = Agent(
    model_name="gpt-4o",
    purpose="To help with various tasks",
    tools=["web", "slack", "notion", "command_line", "image"]
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

## Custom Tools

You can also create your own custom tools. See the [Custom Tools Guide](../examples/using-tools.md) for more information. 