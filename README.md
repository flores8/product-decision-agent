# Tyler

Tyler is an AI chat assistant built with Streamlit and powered by GPT-4. It can converse with users, answer questions, and create plans to perform tasks.

## Prerequisites

- Python 3.12+
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

2. **Install Python with pyenv**
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
├── app_streamlit_chat.py    # Main Streamlit application
├── api.py                  # API server implementation
├── models/
│   ├── TylerAgent.py       # Tyler agent implementation
│   ├── thread.py     # Thread model
│   └── message.py         # Message model
├── prompts/
│   └── TylerPrompt.py     # Prompt templates and configurations
├── tools/                 # Tool implementations
│   ├── command_line.py
│   ├── notion.py
│   └── slack.py
├── utils/                 # Utility functions
│   ├── helpers.py
│   └── tool_runner.py
├── datasets/             # Data storage
├── tests/               # Test suite
└── .github/            # GitHub workflows and configurations
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

## Feedback Logging

The application supports feedback logging through Weights & Biases (wandb). Users can provide feedback on AI responses using thumbs up (👍) or thumbs down (👍) buttons. This feedback is logged and can be used to improve the model's performance over time.

### How it works:
1. Each AI response includes feedback buttons
2. Clicking a feedback button logs the reaction to Weights & Biases
3. Feedback is associated with the specific model call for tracking and analysis
