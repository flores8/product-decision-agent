# Tyler

Tyler is an AI chat assistant built with Streamlit and powered by GPT-4. It can converse with users, answer questions, and create plans to perform tasks.

## Prerequisites

- Python 3.12.8
- pyenv (for Python version management)
- pip (Python package manager)

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

2. **Install Python 3.12.8 with pyenv**
   ```bash
   pyenv install 3.12.8
   ```

3. **Create a virtual environment**
   ```bash
   # Create and activate a new virtual environment for Tyler
   pyenv virtualenv 3.12.8 tyler-env
   pyenv local tyler-env
   ```

4. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tyler.git
   cd tyler
   ```

5. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

6. **Set up secrets**
   
   Create a `.streamlit/secrets.toml` file:
   ```toml
   OPENAI_API_KEY = "your-openai-api-key"
   NOTION_TOKEN = "your-notion-token"  # Optional: Only if using Notion integration
   WANDB_API_KEY = "your-wandb-api-key"  # Optional: Only if using Weights & Biases
   SLACK_BOT_TOKEN = "your-slack-bot-token"  # Optional: Only if using Slack integration
   SLACK_SIGNING_SECRET = "your-slack-signing-secret"  # Optional: Only if using Slack integration
   ```

   Note: Make sure to add `.streamlit/secrets.toml` to your `.gitignore` file to keep your secrets secure.

7. **Run the application**
   ```bash
   streamlit run app_streamlit_chat.py
   ```

   The application will be available at `http://localhost:8501`

## Project Structure

```
tyler/
├── app.py                 # Main Streamlit application
├── models/
│   └── Tyler.py          # Tyler model implementation
├── prompts/
│   └── Tyler.py          # Prompt templates and configurations
├── tools/                 # Tool implementations
│   ├── command_line.py
│   └── notion.py
├── utils/                 # Utility functions
│   ├── helpers.py
│   └── tool_runner.py
└── tests/                 # Test suite
```

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

- **send_message**: Sends messages to specified Slack channels or users
- **create_channel**: Creates a new Slack channel
- **invite_users**: Invites users to a specified channel
- **get_channel_history**: Retrieves message history from a channel

### Command Line Tools (`tools/command_line.py`)
Enables execution of system commands and file operations.

- **execute_command**: Runs shell commands safely in a controlled environment
- **read_file**: Reads contents from specified files
- **write_file**: Writes or updates file contents
- **list_directory**: Lists files and directories in a specified path
