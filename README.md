# Tyler

<div align="center">
    <img src="docs/static/img/tyler-soap.png" alt="Tyler Logo" width="200" style="border-radius: 8px;"/>
</div>

### A framework for manifesting AI agents with a complete lack of conventional limitations

Building a succesful agent requires more than just making llm calls with tools.  Tyler comes with a set of core components that work together to help you get your agent up and running quickly.

---

<div style="display: flex; align-items: center; gap: 20px;">
    <span style="font-size: 1em;">Sponsored by</span>
    <a href="https://weave-docs.wandb.ai/"><img src="docs/static/img/weave_logo.png" alt="Weights & Biases Logo" height="40"/></a>
</div>

---

### For detailed documentation and guides, visit our [Documentation](https://adamwdraper.github.io/tyler/docs/intro).

While Tyler can be used as a library, it also has a web-based chat interface that allows you to interact with your agent. The interface is available as a separate repository at [tyler-chat](https://github.com/adamwdraper/tyler-chat).

![Workflow Status](https://github.com/adamwdraper/tyler/actions/workflows/pytest.yml/badge.svg)
[![PyPI version](https://img.shields.io/pypi/v/tyler-agent.svg?style=social)](https://pypi.org/project/tyler-agent/)

## Overview

### Key Features

- **Persistent Storage**: Choose between in-memory, SQLite, or PostgreSQL storage
- **File Handling**: Process and store files with automatic content extraction
- **Integrations**: Connect with Slack, Notion, and other services
- **Metrics Tracking**: Monitor token usage, latency, and performance
- **Extensible**: Add custom tools and capabilities
- **Async Support**: Built for high-performance async operations
- **Tracing & Debugging**: Built-in support for [W&B Weave](https://weave-docs.wandb.ai/) to track, analyze, and debug agent actions

### Core Components

#### Agent
The central component that manages conversations and executes tasks:
- Uses LLMs for natural language understanding and generation
- Can be customized with specific purposes and tools
- Handles conversation flow and tool execution
- Tracks metrics and performance

#### Tools
Extensible set of capabilities the agent can use:
- Web tools for fetching and processing content
- File processing for various document types
- Integration with services like Slack and Notion
- Custom tool support for specific needs

#### Threads
Conversations are organized into threads:
- Maintains message history and context
- Supports system prompts for setting behavior
- Can be stored in memory, SQLite, or PostgreSQL
- Includes metadata like creation time and attributes
- Can be tagged with sources (e.g., Slack, Notion)

#### Messages
Individual interactions within a thread:
- Supports text and multimodal content (images)
- Can include file attachments
- Tracks metrics like token usage and latency
- Maintains sequence order for conversation flow

#### Attachments
Files and media that can be included in messages:
- Supports PDFs, images, and other file types
- Automatic processing and text extraction
- Secure file storage with configurable backends
- Maintains original files and processed content

## User Guide

### Prerequisites

- Python 3.12.8
- pip (Python package manager)

### Installation

```bash
# Install required libraries for PDF and image processing
brew install libmagic poppler

# Install Tyler (includes all core dependencies)
pip install tyler-agent
```

# For development installation:
```bash
pip install tyler-agent[dev]
```

When you install Tyler using pip, all required runtime dependencies will be installed automatically, including:
- LLM support (LiteLLM, OpenAI)
- Database support (PostgreSQL, SQLite)
- Monitoring and metrics (Weave, Wandb)
- File processing (PDF, images)
- All core utilities and tools

### Basic Setup

Create a `.env` file in your project directory with the following configuration:
```bash
# Database Configuration
TYLER_DB_TYPE=postgresql
TYLER_DB_HOST=localhost
TYLER_DB_PORT=5432
TYLER_DB_NAME=tyler
TYLER_DB_USER=tyler
TYLER_DB_PASSWORD=tyler_dev

# Optional Database Settings
TYLER_DB_ECHO=false
TYLER_DB_POOL_SIZE=5
TYLER_DB_MAX_OVERFLOW=10
TYLER_DB_POOL_TIMEOUT=30
TYLER_DB_POOL_RECYCLE=1800

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Logging Configuration
WANDB_API_KEY=your-wandb-api-key

# Optional Integrations
NOTION_TOKEN=your-notion-token
SLACK_BOT_TOKEN=your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret

# File storage configuration
TYLER_FILE_STORAGE_TYPE=local
TYLER_FILE_STORAGE_PATH=/path/to/files  # Optional, defaults to ~/.tyler/files

# Other settings
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

Only the `OPENAI_API_KEY` (or whatever LLM provider you're using) is required for core functionality. Other environment variables are required only when using specific features:
- For Weave monitoring: `WANDB_API_KEY` is required (You will want to use this for monitoring and debugging) [https://weave-docs.wandb.ai/](Weave Docs)
- For Slack integration: `SLACK_BOT_TOKEN` is required
- For Notion integration: `NOTION_TOKEN` is required
- For database storage:
  - By default uses in-memory storage (perfect for scripts and testing)
  - For PostgreSQL: Database configuration variables are required
  - For SQLite: Will be used as fallback if PostgreSQL settings are incomplete
- For file storage: Defaults will be used if not specified

For more details about each setting, see the [Environment Variables](#environment-variables) section.

### LLM Provider Support

Tyler uses LiteLLM under the hood, which means you can use any of the 100+ supported LLM providers by simply configuring the appropriate environment variables. Some popular options include:

```bash
# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key

# Azure OpenAI
AZURE_API_KEY=your-azure-api-key
AZURE_API_BASE=your-azure-endpoint
AZURE_API_VERSION=2023-07-01-preview

# Google VertexAI
VERTEX_PROJECT=your-project-id
VERTEX_LOCATION=your-location

# AWS Bedrock
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION_NAME=your-region
```

When initializing an Agent, you can specify any supported model using the standard model identifier:

```python
# OpenAI
agent = Agent(model_name="gpt-4")

# Anthropic
agent = Agent(model_name="claude-2")

# Azure OpenAI
agent = Agent(model_name="azure/your-deployment-name")

# Google VertexAI
agent = Agent(model_name="chat-bison")

# AWS Bedrock
agent = Agent(model_name="anthropic.claude-v2")
```

For a complete list of supported providers and models, see the [LiteLLM documentation](https://docs.litellm.ai/).

### Quick Start

This example uses in-memory storage which is perfect for scripts and testing. 

```python
from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
import asyncio
import os

# Load environment variables from .env file
load_dotenv()

# Initialize the agent (uses in-memory storage by default)
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with general questions"
)

async def main():
    # Create a new thread
    thread = Thread()

    # Add a user message
    message = Message(
        role="user",
        content="What can you help me with?"
    )
    thread.add_message(message)

    # Process the thread
    processed_thread, new_messages = await agent.go(thread)

    # Print the assistant's response
    for message in new_messages:
        if message.role == "assistant":
            print(f"Assistant: {message.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

See the complete examples in the documentation.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0) - see the [LICENSE](LICENSE) file for details.

This means you are free to:
- Share and adapt the work for non-commercial purposes
- Use the software for personal projects
- Modify and distribute the code

But you cannot:
- Use the software for commercial purposes without permission
- Sublicense the code
- Hold the author liable

For commercial use, please contact the author.