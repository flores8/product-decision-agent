# Tyler

Tyler is an AI chat assistant powered by GPT-4. It can converse with users, answer questions, and create plans to perform tasks.

![Workflow Status](https://github.com/adamwdraper/tyler/actions/workflows/pytest.yml/badge.svg)

## Prerequisites

- Python 3.12+
- Docker and Docker Compose (for development)
- pip (Python package manager)
- Poppler (for PDF processing)

## Installation

1. Install Tyler with database support:
```bash
# Basic installation (includes PostgreSQL support)
pip install git+https://github.com/yourusername/tyler.git

# For SQLite (lightweight alternative)
pip install "git+https://github.com/yourusername/tyler.git#egg=tyler[sqlite]"
```

## Development Setup

1. **Install pyenv** (if not already installed)

   ```bash
   curl https://pyenv.run | bash
   ```

   Add to your shell configuration file (~/.bashrc, ~/.zshrc, etc.):
   ```bash
   export PATH="$HOME/.pyenv/bin:$PATH"
   eval "$(pyenv init -)"
   eval "$(pyenv virtualenv-init -)"
   ```

2. **Install Python and create virtual environment**
   ```bash
   pyenv install 3.12.8
   pyenv virtualenv 3.12.8 tyler-env
   pyenv local tyler-env
   ```

3. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tyler.git
   cd tyler
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Start the development database**
   ```bash
   # Start PostgreSQL
   docker-compose up -d
   
   # PostgreSQL will be available at:
   # - localhost:5432
   ```

6. **Set up environment variables**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   Add the following database configuration to your `.env`:
   ```bash
   # Database Configuration (PostgreSQL)
   TYLER_DB_TYPE=postgresql
   TYLER_DB_HOST=localhost
   TYLER_DB_PORT=5432
   TYLER_DB_NAME=tyler
   TYLER_DB_USER=tyler
   TYLER_DB_PASSWORD=tyler_dev
   
   # Optional Database Settings
   TYLER_DB_ECHO=false  # Set to true for SQL query logging
   TYLER_DB_POOL_SIZE=5
   TYLER_DB_MAX_OVERFLOW=10
   
   # Other Required Settings
   OPENAI_API_KEY=your-openai-api-key
   WANDB_API_KEY=your-wandb-api-key
   ```

7. **Run the application**
   ```bash
   streamlit run examples/streamlit_chat.py
   ```

   The application will be available at `http://localhost:8501`

## Database Configuration

Tyler uses PostgreSQL as its default database for optimal performance and scalability. The database configuration can be customized through environment variables:

### PostgreSQL (Recommended)
```python
from tyler.models.agent import Agent
from tyler.database.thread_store import SQLAlchemyThreadStore

# PostgreSQL is used by default when no URL is provided
store = SQLAlchemyThreadStore()

# Or explicitly with configuration:
store = SQLAlchemyThreadStore(
    "postgresql://tyler:tyler_dev@localhost/tyler"
)
```

### SQLite (Alternative for Simple Deployments)
```python
# Set environment variable
os.environ["TYLER_DB_TYPE"] = "sqlite"

# Or specify SQLite URL directly
store = SQLAlchemyThreadStore(
    "sqlite:///~/.tyler/data/tyler.db"
)
```

### Environment Variables
The following environment variables can be used to configure the database:
- `TYLER_DB_TYPE`: Database type ("postgresql" or "sqlite")
- `TYLER_DB_HOST`: Database host (default: "localhost")
- `TYLER_DB_PORT`: Database port (default: "5432")
- `TYLER_DB_NAME`: Database name (default: "tyler")
- `TYLER_DB_USER`: Database user (default: "tyler")
- `TYLER_DB_PASSWORD`: Database password
- `TYLER_DB_ECHO`: Enable SQL query logging (default: "false")
- `TYLER_DB_POOL_SIZE`: Connection pool size (default: 5)
- `TYLER_DB_MAX_OVERFLOW`: Maximum pool overflow (default: 10)

## Usage

```python
from tyler.models.agent import Agent
from tyler.database.thread_store import SQLAlchemyThreadStore

# Initialize with your database (choose one):

# SQLite (simplest)
store = SQLAlchemyThreadStore("sqlite:///~/.tyler/data/tyler.db")

# PostgreSQL
# store = SQLAlchemyThreadStore("postgresql://user:pass@localhost/tyler_db")

# MySQL
# store = SQLAlchemyThreadStore("mysql://user:pass@localhost/tyler_db")

# Create agent
agent = Agent(
    thread_store=store,
    model_name="gpt-4o",
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

## Environment Variables

All configuration is managed through environment variables. Create a `.env` file in your project root:

Required:
```bash
OPENAI_API_KEY=your-openai-api-key # Or api key from other LLM providers
WANDB_API_KEY=your-wandb-api-key # For logging calls with Weights & Biases
```

Optional:
```bash
NOTION_TOKEN=your-notion-token  # Only if using Notion integration
SLACK_BOT_TOKEN=your-slack-bot-token  # Only if using Slack integration
SLACK_SIGNING_SECRET=your-slack-signing-secret  # Only if using Slack integration
```

Note: The `.env` file is automatically ignored by git to keep your secrets secure.

## Project Structure

```
tyler/
├── examples/
│   ├── streamlit_chat.py     # Streamlit chat application
│   ├── api.py               # API usage example
│   ├── basic.py            # Basic usage example
│   └── with_tools.py       # Example with custom tools
├── tyler/
│   ├── models/
│   │   ├── agent.py        # Base agent class
│   │   └── thread.py       # Thread model
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

### RouterAgent (`models/routerAgent.py`)
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
- Supports multiple database backends (SQLite, PostgreSQL, MySQL)
- Handles thread persistence and retrieval
- Manages message history

## Running Tests

```bash
pytest
```

## Available Tools

### Notion Integration (`tools/notion.py`)
Enables interaction with Notion workspaces and databases.

- **create_page**: Creates a new page in a specified Notion database
- **search_pages**: Searches for pages in Notion using provided query parameters
- **update_page**: Updates the content of an existing Notion page
- **delete_page**: Deletes a specified page from Notion

### Slack Integration (`tools/slack.py`) 
Provides functionality to interact with Slack workspaces.

#### Local Development Setup
```bash
# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install LocalTunnel
npm install -g localtunnel
```

#### Starting the api server

```bash
# Terminal 1: Start the Flask server
python api.py
```

#### Starting LocalTunnel

```bash
# Terminal 2: Start LocalTunnel to receive events from Slack
lt --port 3000 --subdomain company-of-agents-local-tyler
```

Use the provided LocalTunnel URL (https://xxxx.loca.lt/slack/events) in your Slack App's Event Subscriptions settings.

### Command Line Tools (`tools/command_line.py`)
Enables execution of system commands and file operations.

- **execute_command**: Runs shell commands safely in a controlled environment
- **read_file**: Reads contents from specified files
- **write_file**: Writes or updates file contents
- **list_directory**: Lists files and directories in a specified path

### Web Tools (`tools/web.py`)
Provides functionality to fetch web content and download files.

- **fetch_page**: Fetches content from web pages
  - Supports both text and HTML output formats
  - Cleans and structures content for readability
  - Handles headers for authenticated requests
  - Returns status, content, and error information

- **download_file**: Downloads files from URLs
  - Automatically creates a downloads directory
  - Smart filename detection from URL or Content-Disposition
  - Supports custom headers for authenticated downloads
  - Returns download status, file info, and path

## Feedback Logging

The application supports feedback logging through Weights & Biases (wandb). Users can provide feedback on AI responses using thumbs up (👍) or thumbs down (👍) buttons. This feedback is logged and can be used to improve the model's performance over time.

### How it works:
1. Each AI response includes feedback buttons
2. Clicking a feedback button logs the reaction to Weights & Biases
3. Feedback is associated with the specific model call for tracking and analysis

### Command Line Tools (`tools/command_line.py`)
Enables execution of system commands and file operations.

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

## Development Guidelines

### Adding New Agents

1. Create a new agent class inheriting from `Agent`
2. Define the agent's purpose and system prompt
3. Register the agent in the `Registry`
4. Add any specialized tools the agent needs

Example:
```python
from tyler.models.agent import Agent

class CustomAgent(Agent):
    def __init__(self, **data):
        super().__init__(
            purpose="To handle specific tasks",
            notes="Additional context for the agent",
            **data
        )

### Adding New Tools

1. Create a new tool file in the `tools/` directory
2. Define the tool's interface and implementation in the same format as built-in tools
3. Add tests for the tool functionality

### Using Tools with Agents

Tools must be explicitly specified when creating an agent. You can use both built-in tool modules (specified by name) and custom tools:

```python
def custom_tool_implementation(param1: str) -> str:
    """
    Implement the actual functionality of your tool.
    This function will be called when the tool is used.
    """
    return f"Processed {param1}"

# Define a custom tool with both definition and implementation
custom_tool = {
    # The OpenAI function definition that the LLM will use
    "definition": {
        "type": "function",
        "function": {
            "name": "custom_tool",
            "description": "Description of what the tool does",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Description of parameter"
                    }
                },
                "required": ["param1"]
            }
        }
    },
    # The actual implementation that will be called
    "implementation": custom_tool_implementation
}

# Initialize agent with both built-in and custom tools
agent = Agent(
    purpose="Agent's purpose",
    tools=[
        "web",          # Load the web tools module
        "slack",        # Load the slack tools module
        "command_line", # Load the command line tools module
        custom_tool     # Add your custom tool
    ]
)
```

Available built-in tool modules:
- `web`: Tools for web browsing and file downloads
- `slack`: Tools for Slack integration
- `notion`: Tools for Notion integration
- `command_line`: Tools for safe command line operations
- `file_processor`: Tools for processing various file types

### Creating Built-in Tools

Built-in tools should follow the same format as custom tools. Create a module in the `tools/` directory:

```python
# tools/my_tools.py

@weave.op()
def my_tool_implementation(param1: str) -> str:
    """Implementation of the tool"""
    return f"Processed {param1}"

# Define tools with both definition and implementation
MY_TOOLS = [
    {
        "definition": {
            "type": "function",
            "function": {
                "name": "my-tool",
                "description": "Description of what the tool does",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Description of parameter"
                        }
                    },
                    "required": ["param1"]
                }
            }
        },
        "implementation": my_tool_implementation
    }
]
```

Key points about tools:
- Each tool must provide both its definition (for the LLM) and implementation
- Tools must be explicitly specified in the agent's `tools` parameter
- Built-in tools are loaded by module name (e.g., "web", "slack")
- Custom tools can be provided directly in the tools list
- Tool implementations should be decorated with `@weave.op()`
- Tool definitions must follow the OpenAI function calling format

## Testing

### Test Structure
- Unit tests for individual components
- Integration tests for agent-tool interactions
- End-to-end tests for complete workflows

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/models/test_agent.py

# Run with coverage report
pytest --cov=./ --cov-report=html
```

## Deployment

### Production Setup
1. Set up a production server with Python 3.12+
2. Configure environment variables in `.env` file
3. Set up a process manager (e.g., supervisord)
4. Configure SSL/TLS for secure communications
5. Set up monitoring and logging

### Environment Variables
Create a `.env` file based on `.env.example` with the following variables:

Required:
- `OPENAI_API_KEY`: OpenAI API key for GPT-4 access
- `WANDB_API_KEY`: For logging feedback with Weights & Biases

Optional:
- `NOTION_TOKEN`: For Notion integration
- `SLACK_BOT_TOKEN`: For Slack bot functionality
- `SLACK_SIGNING_SECRET`: For Slack event verification
- `LOG_LEVEL`: Logging level (default: INFO)

Note: Never commit the `.env` file to version control. Use `.env.example` as a template.

## File Processing

The system includes advanced file processing capabilities using GPT-4 Vision and text extraction:

### Supported File Types
- PDF documents (both text-based and scanned)
- Images (JPEG, PNG, GIF, WebP)

### Features
- Smart hybrid processing for PDFs:
  - Fast text extraction for text-based PDFs
  - Vision API fallback for scanned pages
  - Mixed-mode processing for PDFs with both text and scanned pages
- Intelligent image analysis:
  - High-level document/image overview
  - Detailed text extraction with layout preservation
  - Metadata extraction (size, format)

### Example Use Cases
- Extract dates from documents
- Find amounts in invoices
- Analyze document structure and content
- Extract text while preserving formatting
- Answer questions about document content

### Dependencies
For PDF processing, you need to install Poppler:

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils

# CentOS/RHEL
sudo yum install poppler-utils
```

### Python Dependencies
The following packages are required (included in requirements.txt):
- python-magic: For file type detection
- PyPDF2: For PDF text extraction
- pdf2image: For converting PDFs to images
- Pillow: For image processing

### Usage Example
```python
from tyler.tools.file_processor import FileProcessor

# Initialize processor
processor = FileProcessor()

# Process a file
with open('document.pdf', 'rb') as f:
    result = processor.process_file(f.read(), 'document.pdf')

# Access results
if 'error' not in result:
    if result['type'] == 'pdf':
        print(f"PDF content: {result['text']}")
        if result.get('vision_text'):
            print(f"Scanned page content: {result['vision_text']}")
    else:  # image
        print(f"Overview: {result['overview']}")
        print(f"Detailed text: {result['text']}")
```

### File Processing Flow

The system handles attachments through a seamless conversation flow:

1. **Adding Attachments to Messages**
```python
# User sends a message with an attachment
message = Message(
    role="user",
    content="What is the date on this invoice?",
    filename="invoice.pdf",
    file_content=pdf_bytes  # This automatically creates an Attachment
)
thread.add_message(message)
```

2. **Automatic Processing**
- When the agent receives a message, it automatically:
  - Detects any attachments
  - Processes them using the appropriate method (text extraction, vision API)
  - Stores the processed content with the attachment
  - Includes the content in the conversation context

3. **Conversation Flow Example**
```python
# 1. User sends message with attachment
thread.add_message(Message(
    role="user",
    content="What is the date on this invoice?",
    filename="invoice.pdf",
    file_content=pdf_bytes
))

# 2. Agent processes the message
agent.go(thread.id)

# 3. What the LLM sees:
"""
User: What is the date on this invoice?

--- File: invoice.pdf ---
Overview: This is an invoice from Acme Corp...
Content: INVOICE
Date: January 15, 2024
...
"""

# 4. LLM responds using the attachment content
"The invoice is dated January 15, 2024. I found this date clearly marked at the top of the document."
```

4. **Benefits**
- Immediate processing of attachments when received
- Automatic inclusion of attachment content in conversation context
- Natural references to attachment content in responses
- Preservation of original files and processed content
- Support for follow-up questions about the same attachment

5. **Processing Results**
The processed attachment content is stored in a structured format:
```python
{
    "type": "pdf",  # or "image"
    "text": "Extracted text content...",
    "overview": "High-level analysis...",  # for images
    "pages": 1,  # for PDFs
    "empty_pages": [],  # for PDFs with non-extractable pages
    "vision_text": "Text from scanned pages..."  # for PDFs with scanned content
}
```

This processed content is automatically included in the conversation context, allowing the agent to:
- Answer questions about the attachments
- Reference specific parts of the content
- Handle multiple attachments in the same conversation
- Maintain context for follow-up questions
```

