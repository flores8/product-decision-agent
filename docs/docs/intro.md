---
sidebar_position: 1
---

# Introduction to Tyler

Tyler is a powerful AI Agent framework powered by Large Language Models (LLMs). It provides a flexible and extensible platform for building AI assistants that can converse, answer questions, and use tools to perform tasks.

## Key Features

- **Powerful LLM Integration**: Built-in support for 100+ LLM providers through LiteLLM
- **Persistent Storage**: Choose between in-memory, SQLite, or PostgreSQL storage
- **File Handling**: Process and store files with automatic content extraction
- **Service Integrations**: Connect with Slack, Notion, and other services
- **Metrics Tracking**: Monitor token usage, latency, and performance
- **Extensible Tools**: Add custom capabilities to your AI agents
- **Async Support**: Built for high-performance async operations

## Quick Start

### Prerequisites

- Python 3.12.8
- pip (Python package manager)

### Installation

```bash
# Install required libraries for PDF and image processing
brew install libmagic poppler

# Install Tyler
pip install tyler-agent
```

### Basic Usage

Here's a simple example to get you started:

```python
from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
import asyncio
import os

# Load environment variables
load_dotenv()

# Initialize the agent
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

## Next Steps

- [Installation Guide](./installation.md) - Detailed installation instructions
- [Configuration](./configuration.md) - Learn about configuration options
- [Core Concepts](./core-concepts.md) - Understand Tyler's architecture
- [API Reference](./category/api-reference) - Explore the API documentation
- [Examples](./category/examples) - See more usage examples
