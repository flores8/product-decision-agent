# Tyler

A framework for manifesting AI agents with a complete lack of conventional limitations

![Workflow Status](https://github.com/adamwdraper/tyler/actions/workflows/pytest.yml/badge.svg)

## Overview

Tyler is built around several core components that work together to create a powerful and flexible AI assistant:

### Core Components

#### Agent
The central component that manages conversations and executes tasks:
- Uses LLMs for natural language understanding and generation
- Can be customized with specific purposes and tools
- Handles conversation flow and tool execution
- Tracks metrics and performance

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

#### Tools
Extensible set of capabilities the agent can use:
- Web tools for fetching and processing content
- File processing for various document types
- Integration with services like Slack and Notion
- Custom tool support for specific needs

### Key Features

- **Persistent Storage**: Choose between in-memory, SQLite, or PostgreSQL storage
- **File Handling**: Process and store files with automatic content extraction
- **Integrations**: Connect with Slack, Notion, and other services
- **Metrics Tracking**: Monitor token usage, latency, and performance
- **Extensible**: Add custom tools and capabilities
- **Async Support**: Built for high-performance async operations

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

### Additional Examples

#### Database Storage
Tyler supports multiple storage backends including in-memory (default), SQLite, and PostgreSQL. Database storage enables persistence between sessions and is recommended for production use.

**Setup Requirements:**
- Docker (optional, for running PostgreSQL)
- Database initialization

**PostgreSQL Setup:**

1. Create a project directory and install Tyler:
```bash
# Create a directory for your project
mkdir my_tyler_project && cd my_tyler_project

# Set up your preferred Python virtual environment
# and activate it

# Install Tyler (includes PostgreSQL and SQLite support)
pip install tyler-agent
```

2. Set up your environment configuration:
```bash
# Download example environment file
curl -O https://raw.githubusercontent.com/adamwdraper/tyler/main/.env.example
cp .env.example .env
# Edit .env with your desired settings (these will be used by both Tyler and Docker)
```

3. Start PostgreSQL with Docker:
```bash
# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/adamwdraper/tyler/main/docker-compose.yml

# Pull and start PostgreSQL container (uses values from .env automatically)
docker compose up -d postgres

# Initialize the database (uses the same .env values)
python -m tyler.database.cli init
```

That's it! Your PostgreSQL database is ready to use with Tyler.

**Note:** The default values will work out of the box if you don't modify them:
- Database: tyler
- User: tyler
- Password: tyler_dev
- Port: 5433 (mapped to PostgreSQL's default 5432 port inside the container)

4. Optional: Verify the database is running:
```bash
docker compose ps
docker compose logs postgres
```

**SQLite Setup (no Docker needed):**
```bash
# Install Tyler with SQLite dependencies
pip install git+https://github.com/adamwdraper/tyler.git

# Initialize SQLite database
# Uses default location (~/.tyler/data/tyler.db)
python -m tyler.database.cli init --db-type sqlite

# Or specify custom location:
python -m tyler.database.cli init --db-type sqlite --sqlite-path ./my_database.db
```

See the complete example in [`examples/4-database_storage.py`](examples/4-database_storage.py)

#### Full Configuration
Shows how to configure an agent with all available options including custom tools, storage, and behavior settings.

**Setup Requirements:**
- Weave account for monitoring (optional)
- Environment variables in `.env`

See the complete example in [`examples/3-full_configuration.py`](examples/3-full_configuration.py)

#### File Storage
Tyler supports persistent file storage for attachments with automatic content extraction and processing.

**Key Features:**
- Configurable storage backend
- Automatic file processing
- Support for PDFs, images, and other file types
- Sharded directory structure for efficient storage

**Setup Requirements:**
- Poppler (for PDF processing)
- Storage configuration in `.env` (optional)

See the complete example in [`examples/6-file_storage.py`](examples/6-  file_storage.py)

### Available Tools

Tyler comes with several built-in tools and supports custom tool creation:

#### Built-in Tools
- **Web Tools:**
  - Fetch and process web content
  - Download files from URLs
  - Extract text from web pages
  - Process various file types

- **Command Line Tools:**
  - Execute shell commands
  - Run system operations
  - Process command output
  - Handle background tasks

- **Slack Integration:**
  - Send and receive messages
  - Handle user interactions
  - Process file attachments
  - Manage conversations
  - **Configuration:**
    ```bash
    SLACK_BOT_TOKEN=xoxb-your-bot-token
    SLACK_SIGNING_SECRET=your-signing-secret
    ```

- **Notion Integration:**
  - Read and write pages
  - Manage databases
  - Handle blocks and content
  - Process documents
  - **Configuration:**
    ```bash
    NOTION_TOKEN=your-integration-token
    ```

#### Custom Tool Support
- Create synchronous or asynchronous tools
- Use built-in tool modules as building blocks
- Define custom tool schemas and implementations
- Extend functionality with your own tools

See the complete example in [`examples/2-custom_tools.py`](examples/2-custom_tools.py)

### Building Custom Tools

Tyler supports two main types of custom tools: standard tools and interrupt tools. Here's how to implement each:

#### Standard Tools

Standard tools are functions that perform specific tasks and return results. They will be called by the agent and the agent will continue to proceed with its task after the tool has been called. They can be either synchronous or asynchronous:

```python
# Define a synchronous tool implementation
def get_weather_implementation(location: str) -> str:
    """Implementation of the weather tool."""
    return f"The weather in {location} is sunny with a temperature of 72°F"

# Define an asynchronous tool implementation
async def get_weather_async_implementation(location: str) -> str:
    """Async implementation of the weather tool."""
    await asyncio.sleep(1)
    return f"The weather in {location} is sunny with a temperature of 72°F (async)"

# Tool definition with schema
weather_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and country"
                    }
                },
                "required": ["location"]
            }
        }
    },
    "implementation": get_weather_implementation
}

# Use the tool when creating an agent
agent = Agent(
    model_name="gpt-4",
    purpose="To help with weather information",
    tools=[weather_tool]
)
```

#### Interrupt Tools

Interrupt tools are special tools that can interrupt the normal flow of conversation to handle specific situations (like content moderation, user confirmation, etc.).  When called these tools will immidiately stop the agent from proceeding until it recieves further instructions.  They are marked with `"type": "interrupt"` in attributes:

```python
# Define an interrupt tool for content moderation
harmful_content_review = {
    "definition": {
        "type": "function",
        "function": {
            "name": "harmful_content_review",
            "description": "Notifies when potentially harmful content is detected",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Description of the harmful content"
                    },
                    "severity": {
                        "type": "string",
                        "description": "Level of potential harm (high/medium/low)",
                        "enum": ["high", "medium", "low"]
                    },
                    "data": {
                        "type": "object",
                        "description": "Any relevant data about the content"
                    }
                },
                "required": ["message", "severity"]
            }
        }
    },
    "implementation": lambda message, severity="high", data=None: {
        "name": "harmful_content_review",
        "content": json.dumps({
            "type": "harmful_content_detected",
            "message": message,
            "severity": severity,
            "data": data
        })
    },
    "attributes": {
        "type": "interrupt"  # Mark this as an interrupt-type tool
    }
}

# Handle interrupt tool responses
if message.role == "tool" and message.name == "harmful_content_review":
    response_data = json.loads(message.content)
    print(f"Harmful content detected! Severity: {response_data['severity']}")
    print(f"Description: {response_data['message']}")
```

Key differences between standard and interrupt tools:
- Standard tools perform tasks and return results directly and the agent will continue to proceed with its task after the tool has been called.
- Interrupt tools can stop the conversation flow for special handling
- Interrupt tools are marked with `"type": "interrupt"` in attributes
- Interrupt tools typically return structured data for specific handling

For complete examples, see:
- Standard tools: [`examples/2-custom_tools.py`](examples/2-custom_tools.py)
- Interrupt tools: [`examples/5-interrupt_example.py`](examples/5-interrupt_example.py)

## Development Setup

To set up Tyler for development:

1. Clone the repository:
```bash
git clone https://github.com/adamwdraper/tyler.git
cd tyler
```

2. Set up your Python environment:
```bash
# Create and activate your preferred virtual environment

# Install development dependencies
pip install -e ".[dev]"
```

3. Set up pre-commit hooks (recommended):
```bash
pre-commit install
```

4. Run tests:
```bash
pytest
```

### Managing Dependencies

Tyler uses `pip-tools` to manage dependencies:

- `setup.py` defines the core package dependencies
- `requirements.txt` is generated from setup.py for reproducible environments
- `requirements-dev.txt` includes additional development tools

To update dependencies:
```bash
# Update requirements.txt from setup.py
pip-compile setup.py

# Update dev requirements
pip-compile requirements-dev.in

# Install updated requirements
pip-sync requirements.txt requirements-dev.txt
```

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