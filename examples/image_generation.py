#!/usr/bin/env python3
"""
Example demonstrating the use of the image generation tool.
"""
# Load environment variables and configure logging first
from dotenv import load_dotenv
load_dotenv()

# Configure logging before other imports
from tyler.utils.logging import get_logger
logger = get_logger(__name__)

# Now import everything else
import os
import asyncio
import weave
import sys
import json
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message

try:
    if os.getenv("WANDB_API_KEY"):
        weave.init("tyler")
        logger.debug("Weave tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize weave tracing: {e}. Continuing without weave.")

# Initialize the agent with image tools
agent = Agent(
    model_name="gpt-4o",
    purpose="To help create and generate images based on text descriptions.",
    tools=["image"],  # Load the image tools module
    temperature=0.7
)

# Log available tools for debugging
logger.debug(f"Agent initialized with tools: {[tool['function']['name'] for tool in agent._processed_tools]}")

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
        logger.debug("User: %s", user_input)
        
        # Add user message
        message = Message(
            role="user",
            content=user_input
        )
        thread.add_message(message)

        # Process the thread
        processed_thread, new_messages = await agent.go(thread)

        # Log responses
        for message in new_messages:
            if message.role == "assistant":
                logger.debug("Assistant: %s", message.content)
                if message.tool_calls:
                    # Only log tool call metadata, not the full content
                    tool_calls_info = [{
                        "name": tc.get('function', {}).get('name'),
                        "arguments": tc.get('function', {}).get('arguments')
                    } for tc in message.tool_calls]
                    logger.debug("Tool Calls: %s", tool_calls_info)
            elif message.role == "tool":
                try:
                    # Parse the content as JSON since it's now serialized
                    content = json.loads(message.content)
                    if content.get("success"):
                        logger.debug("Tool (%s): Image generated successfully", message.name)
                        logger.debug("Description: %s", content.get("description"))
                        logger.debug("Details: %s", content.get("details"))
                        
                        # Log attachments if present
                        if message.attachments:
                            for attachment in message.attachments:
                                file_info = {
                                    "filename": attachment.filename,
                                    "mime_type": attachment.mime_type,
                                    "description": attachment.processed_content.get("description") if attachment.processed_content else None
                                }
                                logger.debug("Generated file: %s", file_info)
                    else:
                        logger.error("Tool (%s): Error - %s", message.name, content.get("error", "Unknown error"))
                except json.JSONDecodeError:
                    # Handle legacy format or non-JSON content
                    logger.debug("Tool (%s): %s", message.name, message.content)
        
        logger.debug("-" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Exiting gracefully...")
        sys.exit(0) 