#!/usr/bin/env python3

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

# Configure logging
logging.basicConfig(level=logging.INFO)

try:
    if os.getenv("WANDB_API_KEY"):
        weave.init("tyler")
        logger.info("Weave tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize weave tracing: {e}. Continuing without weave.")

# Initialize the agent (uses in-memory storage by default)
agent = Agent(
    model_name="gpt-4o",  # Using latest GPT-4o model
    purpose="To be a helpful assistant that can answer questions and perform tasks.",
    tools=[
        "web",  # Enable web tools for fetching and processing web content
        "command_line"  # Enable command line tools for system operations
    ],
    temperature=0.7  # Control randomness in responses
)

async def main():
    # Create a new thread
    thread = Thread()

    # Add a user message
    message = Message(
        role="user",
        content="Can you help me find information about the weather in San Francisco?"
    )
    thread.add_message(message)

    # Process the thread
    processed_thread, new_messages = await agent.go(thread)

    # Print all assistant responses
    for message in new_messages:
        if message.role == "assistant":
            print(f"\nAssistant: {message.content}")
        elif message.role == "tool":
            print(f"\nTool ({message.name}): {message.content}")

if __name__ == "__main__":
    asyncio.run(main()) 