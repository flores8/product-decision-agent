# Tyler

Tyler is an AI Agent powered by LLMs. It can converse, answer questions, and use tools to perform tasks.

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
# Install Tyler
pip install git+https://github.com/adamwdraper/tyler.git

# Install Poppler (required for PDF processing)
brew install poppler
```

When you install Tyler using pip, all required runtime dependencies will be installed automatically.

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

1. Create a `docker-compose.yml`:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16
    container_name: tyler-postgres
    environment:
      POSTGRES_DB: tyler
      POSTGRES_USER: tyler
      POSTGRES_PASSWORD: tyler_dev
    ports:
      - "5433:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tyler"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

2. Start PostgreSQL:
```bash
docker-compose up -d
```

3. Initialize the database:
```bash
# Using command-line arguments (recommended)
tyler-db init --db-type postgresql \
              --db-host localhost \
              --db-port 5433 \
              --db-name tyler \
              --db-user tyler \
              --db-password tyler_dev

# Or using environment variables in .env:
TYLER_DB_TYPE=postgresql
TYLER_DB_HOST=localhost
TYLER_DB_PORT=5433
TYLER_DB_NAME=tyler
TYLER_DB_USER=tyler
TYLER_DB_PASSWORD=tyler_dev

tyler-db init
```

**SQLite Setup (no Docker needed):**
```bash
# Uses default location (~/.tyler/data/tyler.db)
tyler-db init --db-type sqlite

# Or specify custom location:
tyler-db init --db-type sqlite --sqlite-path ./my_database.db
```

See the complete example in [`examples/database_storage.py`](examples/database_storage.py)

#### Full Configuration
Shows how to configure an agent with all available options including custom tools, storage, and behavior settings.

**Setup Requirements:**
- Weave account for monitoring (optional)
- Environment variables in `.env`

See the complete example in [`examples/full_configuration.py`](examples/full_configuration.py)

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

See the complete example in [`examples/file_storage.py`](examples/file_storage.py)

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

See the complete example in [`examples/with_tools.py`](examples/with_tools.py)