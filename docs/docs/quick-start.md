---
sidebar_position: 3
---

# Quick Start

This guide demonstrates how to create a basic Tyler agent, initialize a conversation thread, and process messages.

## Overview

The quick start guide shows:
- Setting up a Tyler agent
- Creating a conversation thread
- Sending and receiving messages
- Using built-in tools
- Optional Weave monitoring integration

## Basic Example

```python
from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
import asyncio
import weave
import os
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

try:
    if os.getenv("WANDB_API_KEY"):
        weave.init("tyler")
        logger.info("Weave tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize weave tracing: {e}. Continuing without weave.")

# Initialize the agent (uses in-memory storage by default)
agent = Agent(
    model_name="gpt-4o",
    purpose="To be a helpful assistant.",
    tools=[
        "web",
        "slack"
    ]
)

async def main():
    # Create a new thread
    thread = Thread()

    # Add a user message
    message = Message(
        role="user",
        content="What tools do you have?"
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

## Step-by-Step Explanation

### 1. Environment Setup
```python
from dotenv import load_dotenv
load_dotenv()
```
Loads environment variables from your `.env` file, which should contain your API keys and configuration.

### 2. Weave Monitoring (Optional)
```python
try:
    if os.getenv("WANDB_API_KEY"):
        weave.init("tyler")
        logger.info("Weave tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize weave tracing: {e}. Continuing without weave.")
```
Initializes Weave monitoring if a Weights & Biases API key is provided. This is optional but recommended for monitoring in production.

### 3. Agent Initialization
```python
agent = Agent(
    model_name="gpt-4o",
    purpose="To be a helpful assistant.",
    tools=[
        "web",
        "slack"
    ]
)
```
Creates a new Tyler agent with:
- GPT-4 Optimized model
- A general-purpose role
- Web and Slack tools enabled
- Default in-memory storage

### 4. Thread Creation
```python
thread = Thread()
```
Creates a new conversation thread to manage the message history and context.

### 5. Message Creation
```python
message = Message(
    role="user",
    content="What tools do you have?"
)
thread.add_message(message)
```
Creates and adds a user message to the thread.

### 6. Thread Processing
```python
processed_thread, new_messages = await agent.go(thread)
```
Processes the thread using the agent, which:
- Analyzes the messages
- Executes any necessary tools
- Generates responses

### 7. Response Handling
```python
for message in new_messages:
    if message.role == "assistant":
        print(f"Assistant: {message.content}")
```
Prints the assistant's responses from the processed thread.

## Configuration Requirements

### Required Environment Variables
```bash
# .env file
OPENAI_API_KEY=your-openai-api-key
```

### Optional Environment Variables
```bash
# For Weave monitoring
WANDB_API_KEY=your-wandb-api-key

# For Slack integration
SLACK_BOT_TOKEN=your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
```

## Expected Output

When you run this example, you'll see output similar to:

```
Assistant: I have access to the following tools:

1. Web Tools:
   - Fetch and process web content
   - Download files from URLs
   - Extract text from web pages

2. Slack Tools:
   - Send messages to channels
   - Upload files
   - Interact with users
   - Manage conversations

I can use these tools to help you with tasks like:
- Looking up information online
- Processing web content
- Communicating through Slack
- Handling file attachments

Is there anything specific you'd like me to help you with using these tools?
```

## Common Customizations

### Different Model
```python
agent = Agent(
    model_name="gpt-3.5-turbo",  # Use a faster, cheaper model
    purpose="To be a helpful assistant."
)
```

### Additional Tools
```python
agent = Agent(
    model_name="gpt-4o",
    purpose="To be a helpful assistant.",
    tools=[
        "web",
        "slack",
        "notion",
        "command_line"
    ]
)
```

### Custom System Prompt
```python
thread = Thread(
    system_prompt="You are an AI assistant focused on technical support."
)
```

### Message Attributes
```python
message = Message(
    role="user",
    content="Hello!",
    attributes={
        "source": "website",
        "user_id": "123"
    }
)
```

## Next Steps

- Learn about [Using Tools](./examples/using-tools.md)
- Explore [Full Configuration](./examples/full-configuration.md)
- Read the [Core Concepts](./core-concepts.md)
- Check the [API Reference](./category/api-reference) 