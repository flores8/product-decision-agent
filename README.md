# Tyler

Tyler is an AI chat assistant powered by LLMs. It can converse with users, answer questions, and create plans to perform tasks.

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
- Poppler (for PDF processing)

### Installation

```bash
pip install git+https://github.com/adamwdraper/tyler.git
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

### Usage Examples




#### File Storage

Tyler supports persistent file storage for attachments. By default, files are stored in `./data/files` relative to your project root directory, but this can be configured:

1. **Configuration**
   Add to your `.env`:
   ```bash
   # Optional - defaults to 'local'
   TYLER_FILE_STORAGE_TYPE=local
   
   # Optional - defaults to ./data/files in project root
   TYLER_FILE_STORAGE_PATH=/path/to/files
   ```

2. **Usage Example**
   ```python
   from tyler.models.agent import Agent
   from tyler.models.thread import Thread
   from tyler.models.message import Message
   from tyler.storage import init_file_store
   
   # Initialize file storage (optional - will auto-initialize with defaults)
   init_file_store('local', base_path='/custom/path')
   
   # Create agent
   agent = Agent()
   
   # Create thread with file attachment
   thread = Thread()
   message = Message(
       role="user",
       content="Can you analyze this document?",
       file_content=open('document.pdf', 'rb').read(),
       filename='document.pdf'
   )
   thread.add_message(message)
   
   # Process thread - files will be automatically stored
   thread, messages = agent.go(thread)
   ```

3. **File Organization**
   - Files are stored using a sharded directory structure to prevent too many files in one directory
   - Each file gets a unique UUID and is stored as `{base_path}/{uuid[:2]}/{uuid[2:]}`
   - Original filenames and metadata are preserved in the database
   - The default storage location (`./data/files`) will be created automatically if it doesn't exist

4. **Benefits**
   - Reduced database size by not storing base64 content
   - Better file management and organization
   - Support for larger files
   - Original files can be retrieved when needed
   - Files stored alongside your project for easy management

#### Using Database Storage

1. **Install PostgreSQL Dependencies**
   ```bash
   pip install "tyler[postgres]"
   ```

2. **Set Up PostgreSQL with Docker**
   
   Create a `docker-compose.yml`:
   ```yaml
   version: '3.8'
   services:
     db:
       image: postgres:15
       environment:
         POSTGRES_DB: tyler
         POSTGRES_USER: tyler_user
         POSTGRES_PASSWORD: your_password
       ports:
         - "5432:5432"
   ```
   
   Start PostgreSQL:
   ```bash
   docker-compose up -d
   ```

3. **Initialize Database**

   You can initialize in one of two ways:

   **Option 1: Using command-line arguments (recommended)**
   ```bash
   # One command, no env file needed:
   tyler-db init --db-type postgresql \
                 --db-host localhost \
                 --db-port 5432 \
                 --db-name tyler \
                 --db-user tyler_user \
                 --db-password your_password
   ```

   **Option 2: Using environment variables**
   ```bash
   # Create .env file:
   echo "TYLER_DB_TYPE=postgresql
   TYLER_DB_HOST=localhost
   TYLER_DB_PORT=5432
   TYLER_DB_NAME=tyler
   TYLER_DB_USER=tyler_user
   TYLER_DB_PASSWORD=your_password" > .env

   # Then run one of:
   cd backend  # If .env is in backend directory
   tyler-db init

   # Or specify .env path:
   tyler-db init --env-file backend/.env

   # Or use environment variable:
   DOTENV_PATH=backend/.env tyler-db init

   # If you're having trouble with .env loading, add --verbose to see what's happening:
   tyler-db init --verbose
   ```

   **For SQLite (no Docker needed)**
   ```bash
   # Uses default location (~/.tyler/data/tyler.db):
   tyler-db init --db-type sqlite

   # Or specify custom location:
   tyler-db init --db-type sqlite --sqlite-path ./my_database.db
   ```

4. **Use in Your Code**
   
   For scripts and simple applications:
   ```python
   from tyler.models.agent import Agent
   from tyler.database.thread_store import ThreadStore
   import asyncio

   async def main():
       # Create ThreadStore with PostgreSQL URL
       db_url = f"postgresql+asyncpg://{os.getenv('TYLER_DB_USER')}:{os.getenv('TYLER_DB_PASSWORD')}@{os.getenv('TYLER_DB_HOST')}:{os.getenv('TYLER_DB_PORT')}/{os.getenv('TYLER_DB_NAME')}"
       store = ThreadStore(db_url)
       
       # Create agent with persistent storage
       agent = Agent(
           purpose="My purpose",
           thread_store=store
       )
       
       # Your conversations will now persist between sessions
       thread = Thread()
       thread.add_message(Message(role="user", content="Hello!"))
       thread, messages = await agent.go(thread.id)

   if __name__ == "__main__":
       asyncio.run(main())
   ```

   For FastAPI applications:
   ```python
   from fastapi import FastAPI
   from contextlib import asynccontextmanager

   # Create ThreadStore
   db_url = f"postgresql+asyncpg://{os.getenv('TYLER_DB_USER')}:{os.getenv('TYLER_DB_PASSWORD')}@{os.getenv('TYLER_DB_HOST')}:{os.getenv('TYLER_DB_PORT')}/{os.getenv('TYLER_DB_NAME')}"
   thread_store = ThreadStore(db_url)
   
   app = FastAPI()
   ```

### Available Tools

Tyler comes with several built-in tools that agents can use:

#### Web Tools
- Fetch content from web pages
- Download files from URLs
- Process various file types

#### File Processing
Supports processing of:
- PDF documents (text-based and scanned)
- Images (JPEG, PNG, GIF, WebP)
- Text files

#### Slack Integration
For building Slack bots with Tyler:

1. **Configuration**
   Add to your `.env`:
   ```bash
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   SLACK_SIGNING_SECRET=your-signing-secret
   ```

2. **Slack App Settings**
   - Event Subscriptions URL: `https://your-tunnel-name.loca.lt/slack/events`
   - Bot Token Scopes needed:
     - `chat:write`
     - `im:history`
     - `im:write`
     - `app_mentions:read`

#### Notion Integration
For interacting with Notion workspaces:

1. **Configuration**
   Add to your `.env`:
   ```bash
   NOTION_TOKEN=your-integration-token
   ```

---

## Developer Guide

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/adamwdraper/tyler.git
   cd tyler
   ```

2. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"  # This installs the package in editable mode with all development dependencies
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` with your configuration.

4. **Try an example application**
   ```bash
   # Run the Streamlit chat example
   streamlit run examples/streamlit_chat.py
   ```

### Project Structure

```
tyler/
├── examples/              # Example applications
├── tyler/                # Main package
│   ├── models/           # Core models
│   ├── database/         # Database operations
│   ├── tools/            # Built-in tools
│   └── utils/            # Utility functions
└── tests/                # Test suite
```

### Running Tests

```bash
pytest
```

### Core Models

[Rest of the development documentation...]
