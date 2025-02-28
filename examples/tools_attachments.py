#!/usr/bin/env python3
"""
Example demonstrating how to work with attachments in threads.
Shows both manual attachment creation and handling tool-generated attachments.
"""
from dotenv import load_dotenv
load_dotenv()

from tyler.utils.logging import get_logger
logger = get_logger(__name__)

import os
import asyncio
import weave
import sys
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.models.attachment import Attachment
from tyler.database.thread_store import ThreadStore

try:
    if os.getenv("WANDB_API_KEY"):
        weave.init("tyler")
        logger.debug("Weave tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize weave tracing: {e}. Continuing without weave.")

# Initialize the agent with image tools
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with image generation and analysis.",
    temperature=0.7,
    tools=["image"]  # Include image tools for this example
)

# Initialize thread store
thread_store = ThreadStore()

async def example_manual_attachment():
    """Example of manually creating and adding attachments"""
    logger.info("Example 1: Manual Attachment Creation")
    
    # Create a thread
    thread = Thread(title="Thread with Manual Attachments")

    # Create a text file attachment
    text_content = "Hello, this is a sample text file".encode('utf-8')
    text_attachment = Attachment(
        filename="sample.txt",
        content=text_content,
        mime_type="text/plain"
    )

    # Create a message with the attachment
    message = Message(
        role="user",
        content="Here's a text file to analyze",
        attachments=[text_attachment]
    )
    thread.add_message(message)

    # Save the thread - this will process and store the attachment
    await thread_store.save(thread)
    
    logger.info("Created message with text attachment")
    logger.info(f"Attachment status: {text_attachment.status}")
    logger.info(f"Storage path: {text_attachment.storage_path}")
    
    return thread

async def example_tool_generated_attachment():
    """Example of handling attachments generated by tools"""
    logger.info("\nExample 2: Tool-Generated Attachments")
    
    # Create a thread
    thread = Thread(title="Thread with Tool-Generated Attachments")

    # Add a message requesting image generation
    message = Message(
        role="user",
        content=(
            "Please generate a image in the style of a wood block print of a serene Japanese garden "
            "with a traditional wooden bridge over a koi pond, cherry blossoms in full bloom, "
            "and a small tea house in the background."
        )
    )
    thread.add_message(message)

    # Process the thread - this will trigger image generation
    processed_thread, new_messages = await agent.go(thread)
    
    # The thread is automatically saved by the agent, which processes any attachments
    
    # Log information about generated attachments
    for msg in new_messages:
        if msg.attachments:
            logger.info(f"Message from {msg.role} has {len(msg.attachments)} attachments:")
            for att in msg.attachments:
                logger.info(f"- {att.filename} ({att.mime_type})")
                logger.info(f"  Status: {att.status}")
                logger.info(f"  Storage path: {att.storage_path}")
    
    return processed_thread

async def example_adding_attachment_to_existing_message():
    """Example of adding an attachment to an existing message"""
    logger.info("\nExample 3: Adding Attachment to Existing Message")
    
    # Create a thread with a message
    thread = Thread(title="Thread with Added Attachments")
    message = Message(
        role="user",
        content="Here's some data to analyze"
    )
    thread.add_message(message)

    # Add an attachment to the existing message
    json_content = b'{"key": "value"}'
    message.add_attachment(
        attachment=json_content,
        filename="data.json"
    )

    # Save the thread - this will process and store the new attachment
    await thread_store.save(thread)
    
    logger.info(f"Added JSON attachment to message")
    logger.info(f"Attachment status: {message.attachments[0].status}")
    logger.info(f"Storage path: {message.attachments[0].storage_path}")
    
    return thread

async def main():
    # Initialize thread store
    await thread_store.initialize()
    
    # Run examples
    try:
        thread1 = await example_manual_attachment()
        thread2 = await example_tool_generated_attachment()
        # thread3 = await example_adding_attachment_to_existing_message()
        
    except Exception as e:
        logger.error(f"Error in example: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Exiting gracefully...")
        sys.exit(0) 