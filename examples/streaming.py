#!/usr/bin/env python3

from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
import asyncio
import weave
import os
import logging
import sys

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

# Initialize the agent with streaming enabled
agent = Agent(
    model_name="gpt-4o",  # Using latest GPT-4o model
    purpose="To be a helpful assistant that can answer questions and perform tasks.",
    tools=[
        "web",  # Enable web tools for fetching and processing web content
        "command_line"  # Enable command line tools for system operations
    ],
    temperature=0.7,  # Control randomness in responses
    stream=True  # Enable streaming responses
)

async def print_streaming_message(message_content: str):
    """Print message content with streaming effect"""
    for char in message_content:
        print(char, end='', flush=True)
        await asyncio.sleep(0.01)  # Add small delay for streaming effect
    print()  # New line after message

async def main():
    # Create a new thread
    thread = Thread()

    # Example conversation with multiple turns
    conversations = [
        "Tell me about the benefits of exercise.",
        "What specific exercises are good for beginners?",
        "How often should beginners exercise?"
    ]

    for user_input in conversations:
        print(f"\nUser: {user_input}")
        
        # Add user message
        message = Message(
            role="user",
            content=user_input
        )
        thread.add_message(message)

        # Process the thread
        processed_thread, new_messages = await agent.go(thread)

        # Print responses with streaming effect
        for message in new_messages:
            if message.role == "assistant":
                print("\nAssistant: ", end='', flush=True)
                await print_streaming_message(message.content)
            elif message.role == "tool":
                print(f"\nTool ({message.name}): ", end='', flush=True)
                await print_streaming_message(message.content)
        
        print("\n" + "-"*50)  # Separator between conversations

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
        sys.exit(0) 