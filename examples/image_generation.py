#!/usr/bin/env python3
"""
Example demonstrating the use of the image generation tool.
"""
import os
import asyncio
import weave
import logging
import sys
from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

try:
    if os.getenv("WANDB_API_KEY"):
        weave.init("tyler")
        logger.info("Weave tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize weave tracing: {e}. Continuing without weave.")

# Initialize the agent with image tools
agent = Agent(
    model_name="gpt-4o",
    purpose="To help create and generate images based on text descriptions.",
    tools=["image","slack"],  # Load the image tools module
    temperature=0.7
)

# Log available tools for debugging
logger.info(f"Agent initialized with tools: {[tool['function']['name'] for tool in agent._processed_tools]}")

async def main():
    # Create a thread
    thread = Thread()

    # Example image generation request
    conversations = [
        "Please generate a beautiful, photorealistic image of a serene Japanese garden "
        "with a traditional wooden bridge over a koi pond, cherry blossoms in full bloom, "
        "and a small tea house in the background. Make it look natural and peaceful."
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

        # Print responses
        for message in new_messages:
            if message.role == "assistant":
                print(f"\nAssistant: {message.content}")
                if message.tool_calls:
                    print("\nTool Calls:", message.tool_calls)
            elif message.role == "tool":
                print(f"\nTool ({message.name}): {message.content}")
                # If the tool call was successful and returned an image URL
                if isinstance(message.content, dict) and message.content.get("success"):
                    print("\nImage URL:", message.content.get("image_url"))
        
        print("\n" + "-"*50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
        sys.exit(0) 