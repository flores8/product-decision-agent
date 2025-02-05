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

2. **Create Docker Compose File**
   Create a `docker-compose.yml` file in your project directory:
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

3. **Start PostgreSQL**
   ```bash
   docker-compose up -d
   ```

4. **Configure and Use**
   ```python
   from tyler.models.agent import Agent
   from tyler.database.thread_store import ThreadStore

   # Configure storage with connection URL
   store = ThreadStore("postgresql://tyler_user:your_password@localhost/tyler")

   # Create agent with persistent storage
   agent = Agent(
       purpose="My purpose",
       thread_store=store
   )

   # Your conversations will now persist between sessions
   thread = Thread()
   thread.add_message(Message(role="user", content="Hello!"))
   thread, messages = agent.go(thread)

   # Later, you can retrieve the thread
   saved_thread = store.get(thread.id)
   ```

   Or configure via environment variables in `.env`:
   ```bash
   TYLER_DB_TYPE=postgresql
   TYLER_DB_HOST=localhost
   TYLER_DB_PORT=5432
   TYLER_DB_NAME=tyler
   TYLER_DB_USER=tyler_user
   TYLER_DB_PASSWORD=your_password
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

1. **Clone the repository**
   ```bash
   git clone https://github.com/adamwdraper/tyler.git
   cd tyler
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
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
