---
sidebar_position: 2
---

# Installation Guide

This guide will walk you through the process of installing Tyler and setting up your development environment.

## System Requirements

### Python Version
Tyler requires Python 3.12.8 or later. You can check your Python version by running:

```bash
python --version
```

If you need to install or update Python, visit the [official Python website](https://www.python.org/downloads/).

### System Dependencies
Tyler requires some system libraries for processing PDFs and images:

#### macOS
```bash
brew install libmagic poppler
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y libmagic1 poppler-utils
```

#### Windows
For Windows users, you'll need to:
1. Install [Chocolatey](https://chocolatey.org/install)
2. Install the required packages:
```bash
choco install poppler libmagic
```

## Installation Methods

### From PyPI (Recommended)
Install the latest version from PyPI:

```bash
pip install tyler-agent
```

### Development Installation
For contributing or development:

```bash
# Clone the repository
git clone https://github.com/adamwdraper/tyler.git
cd tyler

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev]"
```

## Configuration

### Environment Variables
Create a `.env` file in your project directory. You can start by copying the example:

```bash
curl -O https://raw.githubusercontent.com/adamwdraper/tyler/main/.env.example
cp .env.example .env
```

Edit the `.env` file with your settings. The minimal required configuration is:

```bash
# OpenAI API Key (or other LLM provider)
OPENAI_API_KEY=your-api-key-here
```

### Optional Dependencies

#### Database Support
For PostgreSQL support:
```bash
pip install "tyler-agent[postgresql]"
```

For SQLite support (included by default):
```bash
# No additional installation needed
```

#### Monitoring
For Weave monitoring support:
```bash
pip install "tyler-agent[monitoring]"
```

#### Service Integrations
For Slack integration:
```bash
pip install "tyler-agent[slack]"
```

For Notion integration:
```bash
pip install "tyler-agent[notion]"
```

## Verifying Installation

You can verify your installation by running a simple test:

```python
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
import asyncio

async def test_installation():
    agent = Agent(
        model_name="gpt-4o",
        purpose="To test the installation"
    )
    thread = Thread()
    message = Message(
        role="user",
        content="Hello! Are you working correctly?"
    )
    thread.add_message(message)
    
    processed_thread, new_messages = await agent.go(thread)
    
    for message in new_messages:
        if message.role == "assistant":
            print(f"Assistant: {message.content}")

if __name__ == "__main__":
    asyncio.run(test_installation())
```

If everything is set up correctly, you should see a response from the AI assistant.

## Troubleshooting

### Common Issues

#### PDF Processing Issues
If you encounter PDF processing errors:
- Verify that Poppler is installed correctly
- Check system PATH includes Poppler binaries
- Try reinstalling Poppler

#### Database Connection Issues
For PostgreSQL connection errors:
- Verify PostgreSQL is running
- Check connection credentials
- Ensure database exists and is accessible

#### API Key Issues
If you get authentication errors:
- Verify your API key is set correctly in `.env`
- Check that `.env` is in the correct directory
- Ensure the API key is valid and has sufficient credits

### Getting Help

If you encounter any issues:
1. Check the [GitHub Issues](https://github.com/adamwdraper/tyler/issues) for similar problems
2. Search the [GitHub Discussions](https://github.com/adamwdraper/tyler/discussions)
3. Create a new issue if your problem hasn't been reported

## Next Steps

- Read the [Configuration Guide](./configuration.md) to learn about available options
- Explore the [Core Concepts](./core-concepts.md) to understand Tyler's architecture
- Try out some [Examples](./category/examples) to learn common usage patterns 