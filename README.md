# Tyler

Tyler is an AI chat assistant powered by GPT-4. It can converse with users, answer questions, and create plans to perform tasks.

![Workflow Status](https://github.com/adamwdraper/tyler/actions/workflows/pytest.yml/badge.svg)

## Prerequisites

- Python 3.12.8
- pip (Python package manager)
- Poppler (for PDF processing)
- Docker and Docker Compose (optional, only if using PostgreSQL for development)

## Installation

Install Tyler:
```bash
pip install git+https://github.com/adamwdraper/tyler.git
```

The database type (PostgreSQL, SQLite, or in-memory) is controlled through environment variables in your `.env` file. See the Database Configuration section for details.

## Development Setup

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

4. **(Optional) Set up PostgreSQL database**
   If you want to use PostgreSQL instead of the default in-memory storage:
   ```bash
   # Start PostgreSQL
   docker-compose up -d
   
   # PostgreSQL will be available at:
   # - localhost:5432
   ```

5. **Try an example application**
   ```bash
   # Run the Streamlit chat example
   streamlit run examples/streamlit_chat.py
   ```

   The chat application will be available at `http://localhost:8501`

   Check the `examples/` directory for other usage examples.

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

## Usage

### Basic Example
```python
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message

# Create agent
agent = Agent(
    purpose="To help with general questions"
)

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

### Advanced Configuration
You can customize the agent's behavior and storage:

```python
from tyler.models.agent import Agent
from tyler.database.thread_store import ThreadStore

# Configure storage (if not using default in-memory)
store = ThreadStore("postgresql://user:pass@localhost/dbname")

# Create agent with custom configuration
agent = Agent(
    purpose="To help with specific tasks",
    thread_store=store,  # Optional - uses in-memory if not provided
    model_name="gpt-4",  # Optional - uses default from environment
    tools=["web", "slack"]  # Optional - specify which tools to enable
)
```

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

All configuration is done through environment variables. See the Development Setup section for the complete list of available options.

The only truly required variable is:
```bash
OPENAI_API_KEY=your-openai-api-key
```

All other variables are optional and depend on which features you want to use.

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

## Feedback Logging

The application supports feedback logging through Weights & Biases (wandb). Users can provide feedback on AI responses using thumbs up (👍) or thumbs down (👎) buttons. This feedback is logged and can be used to improve the model's performance over time.

### How it works:
1. Each AI response includes feedback buttons
2. Clicking a feedback button logs the reaction to Weights & Biases
3. Feedback is associated with the specific model call for tracking and analysis

## Development Guidelines

### Adding New Agents

1. Create a new agent class inheriting from `Agent`:
```python
from tyler.models.agent import Agent

class CustomAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(
            purpose="Your agent's specific purpose",
            **kwargs
        )
```

2. Define the agent's purpose and system prompt in the class
3. Register the agent in the `Registry`:
```python
from tyler.models.registry import Registry

Registry.register("custom", CustomAgent)
```

4. Add any specialized tools the agent needs:
```python
agent = CustomAgent(
    tools=["web", "slack", your_custom_tool]
)
```

### Adding New Tools

1. Create a new tool module in the `tools/` directory
2. Define the tool's interface and implementation:
```python
def custom_tool_implementation(param1: str) -> str:
    """Implement your tool's functionality"""
    return f"Processed {param1}"

CUSTOM_TOOLS = [{
    "definition": {
        "type": "function",
        "function": {
            "name": "custom-tool",
            "description": "What your tool does",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Parameter description"
                    }
                },
                "required": ["param1"]
            }
        }
    },
    "implementation": custom_tool_implementation
}]
```

3. Use the tool with an agent:
```python
from tyler.tools import your_tool_module

agent = Agent(
    purpose="Agent purpose",
    tools=["web", your_tool_module]
)
```

### Testing Guidelines

1. Add tests for new functionality in the `tests/` directory
2. Follow existing test patterns:
   - Unit tests for individual components
   - Integration tests for component interactions
   - Mock external services appropriately
3. Run tests with coverage:
```bash
pytest --cov=tyler tests/
```

## Deployment

### Production Setup

1. **Install Tyler**
   ```bash
   pip install git+https://github.com/adamwdraper/tyler.git
   ```

2. **Configure Environment**
   Create a `.env` file with your configuration:
   ```bash
   # Required
   OPENAI_API_KEY=your-openai-api-key

   # Database (recommended for production)
   TYLER_DB_TYPE=postgresql
   TYLER_DB_HOST=your-db-host
   TYLER_DB_PORT=5432
   TYLER_DB_NAME=tyler
   TYLER_DB_USER=your-db-user
   TYLER_DB_PASSWORD=your-db-password

   # Optional Features
   WANDB_API_KEY=your-wandb-api-key  # For feedback logging
   NOTION_TOKEN=your-notion-token     # For Notion integration
   SLACK_BOT_TOKEN=your-bot-token     # For Slack integration
   SLACK_SIGNING_SECRET=your-secret   # For Slack integration
   LOG_LEVEL=INFO                     # Logging level
   ```

3. **Set Up Process Management**
   Example supervisord configuration (`/etc/supervisor/conf.d/tyler.conf`):
   ```ini
   [program:tyler]
   command=/path/to/venv/bin/python examples/api.py
   directory=/path/to/tyler
   user=tyler
   autostart=true
   autorestart=true
   environment=
       PYTHONPATH="/path/to/tyler",
       PATH="/path/to/venv/bin:%(ENV_PATH)s"
   ```

4. **Security Considerations**
   - Use HTTPS for all external communications
   - Store environment variables securely
   - Set up proper database user permissions
   - Configure firewall rules appropriately
   - Regularly update dependencies

5. **Monitoring**
   - Use standard Python logging (configured via LOG_LEVEL)
   - Monitor database connections and performance
   - Track API rate limits (OpenAI, Slack, etc.)
   - Set up alerts for critical errors

## File Processing

Tyler includes advanced file processing capabilities using GPT-4 Vision and text extraction tools:

### Supported File Types
- PDF documents (both text-based and scanned)
- Images (JPEG, PNG, GIF, WebP)
- Text files (various encodings)

### Features
- Smart hybrid processing for PDFs:
  - Text extraction for text-based PDFs
  - Vision API for scanned documents
  - Mixed-mode for hybrid documents
- Image analysis:
  - Text extraction with layout preservation
  - Content understanding
  - Metadata extraction

### Setup Requirements
1. Install Poppler for PDF processing:
   ```bash
   # macOS
   brew install poppler

   # Ubuntu/Debian
   sudo apt-get install poppler-utils

   # CentOS/RHEL
   sudo yum install poppler-utils
   ```

2. Required Python packages (included in requirements.txt):
   - python-magic: File type detection
   - PyPDF2: PDF text extraction
   - pdf2image: PDF to image conversion
   - Pillow: Image processing

### Usage Example
```python
from tyler.models.agent import Agent
from tyler.models.message import Message
from tyler.models.thread import Thread

# Create agent with file processing capability
agent = Agent(
    purpose="Document analysis assistant",
    tools=["file_processor"]
)

# Create a thread with a file attachment
thread = Thread()
with open('document.pdf', 'rb') as f:
    message = Message(
        role="user",
        content="What's in this document?",
        filename="document.pdf",
        file_content=f.read()
    )
thread.add_message(message)

# Process the document
processed_thread, responses = agent.go(thread.id)

# Get the agent's analysis
for message in responses:
    if message.role == "assistant":
        print(message.content)
```

### Processing Flow
1. File type detection
2. Content extraction using appropriate method
3. Automatic handling of mixed content types
4. Integration with conversation context
5. Support for follow-up questions about the document

## Running Tests

### Quick Start
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=tyler tests/
```

### Test Categories
1. **Unit Tests** (`tests/unit/`)
   - Individual component testing
   - Mock external dependencies
   - Fast execution

2. **Integration Tests** (`tests/integration/`)
   - Component interaction testing
   - Database operations
   - Tool execution

3. **End-to-End Tests** (`tests/e2e/`)
   - Complete workflow testing
   - External service integration
   - Real file processing

### Development Testing
```bash
# Run specific test file
pytest tests/unit/test_agent.py

# Run tests matching pattern
pytest -k "agent"

# Run with detailed output
pytest -v

# Run with logging
pytest --log-cli-level=INFO
```

