# Tyler

Tyler is an AI chat assistant powered by GPT-4. It can converse with users, answer questions, and create plans to perform tasks.

![Workflow Status](https://github.com/adamwdraper/tyler/actions/workflows/pytest.yml/badge.svg)

## Prerequisites

- Python 3.12.8
- pip (Python package manager)
- Poppler (for PDF processing)

## Installation & Quick Start

1. **Install Tyler**
   ```bash
   pip install git+https://github.com/adamwdraper/tyler.git
   ```

2. **Set up environment variables**
   
   Create a `.env` file in your project directory with your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your-openai-api-key  # Required
   ```
   
   That's it! Tyler uses in-memory storage by default. For additional features like persistent storage, monitoring, or integrations, see the [Environment Variables](#environment-variables) section.

3. **Start using Tyler**
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

## Usage Examples

### Basic Chat
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

### With Database Storage
```python
from tyler.models.agent import Agent
from tyler.database.thread_store import ThreadStore

# Configure PostgreSQL storage
store = ThreadStore("postgresql://user:pass@localhost/dbname")

# Or use SQLite
# store = ThreadStore("sqlite:///path/to/your/database.db")

agent = Agent(
    purpose="My purpose",
    thread_store=store
)
```

Check the `examples/` directory in the repository for more usage examples, including:
- Streamlit chat application
- API implementation
- Slack bot integration

## Development Setup

If you want to contribute to Tyler or run it from source:

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
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` with your configuration. See [Environment Variables](#environment-variables) section for details.

4. **(Optional) Set up PostgreSQL database**
   If you want to use PostgreSQL instead of the default in-memory storage:
   ```bash
   # Start PostgreSQL
   docker-compose up -d
   ```

5. **Try an example application**
   ```bash
   # Run the Streamlit chat example
   streamlit run examples/streamlit_chat.py
   ```

## Database Configuration

Tyler supports multiple storage options for conversation history:

### In-Memory Storage (Default)
The simplest way to get started - no configuration needed:
```python
from tyler.models.agent import Agent

# Uses in-memory storage by default
agent = Agent(purpose="My purpose")
```

### PostgreSQL Storage
For production use when persistence is needed:
```python
from tyler.models.agent import Agent
from tyler.database.thread_store import ThreadStore

# Using environment variables from .env
store = ThreadStore()  # Uses TYLER_DB_* environment variables

# Or explicitly with URL:
store = ThreadStore("postgresql://tyler:tyler_dev@localhost/tyler")

agent = Agent(
    purpose="My purpose",
    thread_store=store
)
```

### SQLite Storage
For lightweight persistence without a database server:
```python
from tyler.models.agent import Agent
from tyler.database.thread_store import ThreadStore

store = ThreadStore("sqlite:///path/to/your/database.db")

agent = Agent(
    purpose="My purpose",
    thread_store=store
)
```

All storage options provide the same functionality - choose based on your needs:
- In-Memory: Fastest, but conversations are lost when the program exits
- SQLite: Simple file-based storage, good for development and small applications
- PostgreSQL: Best for production use, supports concurrent access and large datasets

## Available Tools

Tyler comes with several built-in tools that agents can use:

### Web Tools
- Fetch content from web pages
- Download files from URLs
- Process various file types

### File Processing
Supports processing of:
- PDF documents (text-based and scanned)
- Images (JPEG, PNG, GIF, WebP)
- Text files

### Slack Integration
For building Slack bots with Tyler:

1. **Setup**
   ```bash
   # Install development dependencies
   npm install -g localtunnel
   
   # Start the Flask server
   python examples/slack_bot.py
   
   # In another terminal, start LocalTunnel
   lt --port 3000 --subdomain your-tunnel-name
   ```

2. **Configuration**
   Add to your `.env`:
   ```bash
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   SLACK_SIGNING_SECRET=your-signing-secret
   ```

3. **Slack App Settings**
   - Event Subscriptions URL: `https://your-tunnel-name.loca.lt/slack/events`
   - Bot Token Scopes needed:
     - `chat:write`
     - `im:history`
     - `im:write`
     - `app_mentions:read`

### Notion Integration
For interacting with Notion workspaces:

1. **Configuration**
   Add to your `.env`:
   ```bash
   NOTION_TOKEN=your-integration-token
   ```

2. **Available Operations**
   - Create pages
   - Search content
   - Update pages
   - Delete pages

## Environment Variables

All configuration is done through environment variables. The only truly required variable is:
```bash
OPENAI_API_KEY=your-openai-api-key  # Required for all functionality
```

Optional variables based on features used:
```bash
# Feedback Logging (optional)
WANDB_API_KEY=your-wandb-api-key  # Optional - Tyler works without it, but you'll miss monitoring features

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

Tyler will work perfectly fine without any of the optional variables - they are only needed if you want to use specific features like feedback logging, persistent storage, or third-party integrations.

## Project Structure

```
tyler/
├── examples/
│   ├── streamlit_chat.py     # Streamlit chat application
│   ├── api.py               # API usage example
│   ├── basic.py            # Basic usage example
│   └── slack_bot.py        # Slack bot example
├── tyler/
│   ├── models/
│   │   ├── agent.py        # Base agent class
│   │   ├── router_agent.py # Message routing agent
│   │   ├── registry.py     # Agent registry
│   │   ├── thread.py       # Thread model
│   │   └── message.py      # Message model
│   ├── database/
│   │   ├── thread_store.py # Database operations
│   │   └── cli.py         # CLI database tools
│   ├── tools/              # Built-in tools
│   │   ├── web.py
│   │   ├── notion.py
│   │   ├── slack.py
│   │   └── file_processor.py
│   └── utils/              # Utility functions
│       ├── files.py
│       └── tool_runner.py
├── tests/                  # Test suite
└── .github/               # GitHub workflows
```

## Core Models

### Agent (`models/agent.py`)
The base agent class that handles conversations and tool execution. Key features:
- Processes messages using GPT-4 model
- Manages conversation threads and message history
- Executes tools based on conversation context
- Handles recursive tool calls with depth limiting
- Uses a customizable system prompt for different agent purposes

### RouterAgent (`models/router_agent.py`)
A specialized agent responsible for directing incoming messages to appropriate specialized agents:
- Analyzes message content and intent
- Identifies explicit @mentions of agents
- Routes messages to the most suitable agent
- Creates and manages conversation threads
- Maintains thread history and agent assignments

### Registry (`models/registry.py`)
Manages the registration and access of available agents in the system:
- Stores both agent classes and instances
- Handles agent registration with optional configuration
- Provides methods to access and verify agent availability
- Supports dynamic agent instantiation

### Thread (`models/thread.py`)
Represents a conversation thread containing multiple messages:
- Manages message history and ordering
- Handles system prompts
- Tracks thread metadata (creation time, updates)
- Supports source tracking (e.g., Slack threads)
- Provides chat completion API compatibility

### Message (`models/message.py`)
Represents individual messages within a thread:
- Supports multiple message roles (system, user, assistant, tool)
- Handles tool calls and results
- Generates unique message IDs
- Tracks message metadata and source information
- Manages message attributes and timestamps

### Thread Store (`database/thread_store.py`)
Manages the storage and retrieval of conversation threads:
- Supports multiple database backends (SQLite, PostgreSQL)
- Handles thread persistence and retrieval
- Manages message history

## Architecture Overview

Tyler uses a modular architecture built around a few key concepts:

1. **Agents**: The core processing units that handle conversations and execute tasks
   - Base Agent: Handles general conversation and tool execution
   - Router Agent: Routes messages to specialized agents based on content and @mentions
   - Specialized Agents: Handle specific types of tasks (can be added as needed)

2. **Threads**: Conversation containers that maintain message history and context
   - Each thread represents a distinct conversation
   - Threads can be sourced from different platforms (Slack, Web UI, etc.)
   - Messages within threads maintain order and relationships

3. **Tools**: Modular components that agents can use to perform tasks
   - Each tool has a specific purpose and interface
   - Tools can be added or modified without changing agent logic
   - Tools are executed through a standardized tool runner

## Running Tests

```bash
pytest
```

## W&B Weave Integration

Tyler integrates with [Weights & Biases (W&B) Weave](https://weave-docs.wandb.ai/) for comprehensive LLM application monitoring and improvement. Weave is automatically initialized when you create an Agent if `WANDB_API_KEY` is present in your environment variables.

### Configuration
Simply add your W&B API key to your `.env`:
```bash
WANDB_API_KEY=your-wandb-api-key  # Optional - Tyler works without it, but you'll miss monitoring features
```

That's it! No additional code is needed. When you create an Agent, it will automatically:
- Initialize Weave if `WANDB_API_KEY` is present
- Start tracking all LLM calls and agent actions
- Work normally (without monitoring) if `WANDB_API_KEY` is not set

```python
from tyler.models.agent import Agent

# Weave will automatically initialize if WANDB_API_KEY is set
agent = Agent(purpose="My purpose")
```

When Weave is enabled, you get access to:

- **Tracing & Monitoring**: Track all LLM calls and application logic to debug and analyze your system
- **Systematic Iteration**: Refine and iterate on prompts and model configurations
- **Experimentation**: Test different models and prompts in the LLM Playground
- **Evaluation**: Use custom or pre-built scorers to assess application performance
- **Guardrails**: Implement content moderation and prompt safety checks
- **User Feedback**: Collect and analyze user reactions (👍 or 👎) on responses

### Features Available
1. **LLM Call Tracing**
   - Monitor all model interactions
   - Track token usage and costs
   - Analyze response times and performance

2. **Application Insights**
   - Debug conversation flows
   - Monitor tool usage patterns
   - Track system performance

3. **User Feedback Collection**
   - Capture user reactions to responses
   - Analyze feedback patterns
   - Identify areas for improvement

4. **Performance Monitoring**
   - Track model performance metrics
   - Monitor system reliability
   - Analyze usage patterns

Tyler works perfectly fine without W&B Weave integration, but including it gives you powerful tools for monitoring, debugging, and improving your LLM application.

## Development Guidelines

### Adding New Agents

1. Create a new agent class inheriting from `Agent`:
```