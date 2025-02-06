# Tyler

Tyler is an AI chat assistant powered by GPT-4. It can converse with users, answer questions, and create plans to perform tasks.

![Workflow Status](https://github.com/adamwdraper/tyler/actions/workflows/pytest.yml/badge.svg)

## User Guide

### Prerequisites

- Python 3.12.8
- pip (Python package manager)
- Poppler (for PDF processing)

### Installation

```bash
pip install git+https://github.com/adamwdraper/tyler.git
```

That's all you need! When you install Tyler using pip, all required dependencies will be installed automatically.

If you want to use PostgreSQL storage, you'll need to install the PostgreSQL adapter by adding the postgres extras:
```bash
# This installs Tyler with psycopg2-binary, the PostgreSQL adapter for Python
pip install "git+https://github.com/adamwdraper/tyler.git#egg=tyler[postgres]"
```

### Basic Setup

Create a `.env` file in your project directory with your OpenAI API key:
```bash
OPENAI_API_KEY=your-openai-api-key  # Required
```

That's it! Tyler uses in-memory storage by default. For additional features like persistent storage, monitoring, or integrations, see the [Environment Variables](#environment-variables) section.

### Quick Start

```python
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message

# Create agent
agent = Agent(purpose="To help with general questions")

# Create a thread and add a message
thread = Thread()
message = Message(
    role="user",
    content="What can you help me with?"
)
thread.add_message(message)

# Get the agent's response
processed_thread, new_messages = agent.go(thread.id)

# Print the response
for message in new_messages:
    if message.role == "assistant":
        print(message.content)
```

### Usage Examples

#### Basic Chat
```python
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message

# Create agent with custom configuration
agent = Agent(
    purpose="To help with specific tasks",
    model_name="gpt-4",  # Optional - uses default from environment
    tools=["web", "slack"]  # Optional - specify which tools to enable
)

# Start a conversation
thread = Thread()
thread.add_message(Message(role="user", content="Can you help me analyze this PDF?"))

# Get response
thread, messages = agent.go(thread)
```

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

### Environment Variables

All configuration is done through environment variables. The only truly required variable is:
```bash
OPENAI_API_KEY=your-openai-api-key  # Required for all functionality
```

Optional variables based on features used:
```bash
# Monitoring (optional)
WANDB_API_KEY=your-wandb-api-key  # For monitoring and debugging features

# Database Configuration (optional - defaults to in-memory)
TYLER_DB_TYPE=postgresql          # Options: postgresql, sqlite
TYLER_DB_HOST=your-db-host
TYLER_DB_PORT=5432
TYLER_DB_NAME=tyler
TYLER_DB_USER=your-db-user
TYLER_DB_PASSWORD=your-db-password

# Integrations (optional)
NOTION_TOKEN=your-notion-token     # Only needed for Notion integration
SLACK_BOT_TOKEN=your-bot-token     # Only needed for Slack integration
SLACK_SIGNING_SECRET=your-secret   # Only needed for Slack integration

# Other Settings (optional)
LOG_LEVEL=INFO                     # Default: INFO
```

Tyler works perfectly fine without any of the optional variables - they are only needed if you want to use specific features.

---

## Developer Guide

### Development Setup

If you want to contribute to Tyler or develop with the source code:

1. **Clone the repository**
   ```bash
   git clone https://github.com/adamwdraper/tyler.git
   cd tyler
   ```

2. **Install development dependencies**
   ```bash
   # This installs Tyler in editable mode with all development dependencies
   pip install -e ".[dev,postgres]"
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
