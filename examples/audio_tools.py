#!/usr/bin/env python3
"""
Example demonstrating the use of the audio tools for text-to-speech and speech-to-text.
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
import base64
from pathlib import Path
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message
from tyler.database.thread_store import ThreadStore
from tyler.storage import get_file_store

try:
    if os.getenv("WANDB_API_KEY"):
        weave.init("tyler")
        logger.debug("Weave tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize weave tracing: {e}. Continuing without weave.")

# Initialize thread store for persistence
thread_store = ThreadStore()

async def init():
    # Initialize the thread store
    await thread_store.initialize()
    
    # Initialize the agent with audio tools and thread store
    return Agent(
        model_name="gpt-4o",
        purpose="To help convert text to speech and transcribe speech to text.",
        tools=["audio"],  # Load the audio tools module
        temperature=0.7,
        thread_store=thread_store  # Pass thread store to agent
    )

async def text_to_speech_example():
    """Example of text-to-speech conversion"""
    # Initialize agent with thread store
    agent = await init()
    
    # Log available tools for debugging
    logger.debug(f"Agent initialized with tools: {[tool['function']['name'] for tool in agent._processed_tools]}")
    
    # Create a thread
    thread = Thread()

    # Example text-to-speech request
    user_input = (
        "Please convert the following text to speech using the 'nova' voice: "
        "'Hello! This is a demonstration of the text-to-speech capability. "
        "I hope you find this useful for your applications.'"
    )

    logger.debug("User: %s", user_input)
    
    # Add user message
    message = Message(
        role="user",
        content=user_input
    )
    thread.add_message(message)

    # Process the thread - agent will handle saving
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
                    logger.debug("Tool (%s): Audio generated successfully", message.name)
                    logger.debug("Description: %s", content.get("description"))
                    logger.debug("Details: %s", content.get("details"))
                    
                    # Log attachments if present
                    if message.attachments:
                        for attachment in message.attachments:
                            file_info = {
                                "filename": attachment.filename,
                                "mime_type": attachment.mime_type,
                                "file_id": attachment.file_id,
                                "storage_path": attachment.storage_path,
                                "description": attachment.processed_content.get("description") if attachment.processed_content else None
                            }
                            logger.debug("Generated file: %s", file_info)
                            
                            # Verify the file is stored in the file store
                            if attachment.file_id:
                                logger.debug(f"File successfully stored with ID: {attachment.file_id}")
                                
                                # Save a copy to the output directory for demonstration
                                output_dir = Path("./output")
                                output_dir.mkdir(exist_ok=True)
                                
                                # Get the content from the file store
                                file_store = get_file_store()
                                audio_bytes = await file_store.get(attachment.file_id, attachment.storage_path)
                                
                                output_path = output_dir / attachment.filename
                                with open(output_path, "wb") as f:
                                    f.write(audio_bytes)
                                logger.debug(f"Saved audio file to {output_path}")
                else:
                    logger.error("Tool (%s): Error - %s", message.name, content.get("error", "Unknown error"))
            except json.JSONDecodeError:
                # Handle legacy format or non-JSON content
                logger.debug("Tool (%s): %s", message.name, message.content)
    
    logger.debug("-" * 50)
    return processed_thread

async def speech_to_text_example(audio_file_path):
    """Example of speech-to-text transcription"""
    # Initialize agent with thread store
    agent = await init()
    
    # Create a thread
    thread = Thread()

    # Read the audio file
    with open(audio_file_path, "rb") as f:
        audio_bytes = f.read()
    
    # Encode as base64
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    # Example speech-to-text request
    user_input = f"Please transcribe this audio file to text."
    
    logger.debug("User: %s", user_input)
    
    # Add user message with audio attachment
    message = Message(
        role="user",
        content=user_input,
        attachments=[{
            "filename": os.path.basename(audio_file_path),
            "content": audio_base64,
            "mime_type": "audio/mp3"  # Adjust based on your file type
        }]
    )
    thread.add_message(message)

    # Ensure the attachment is stored
    await message.ensure_attachments_stored()
    logger.debug(f"Attachment stored with ID: {message.attachments[0].file_id}")

    # Process the thread
    processed_thread, new_messages = await agent.go(thread)

    # Log responses
    for message in new_messages:
        if message.role == "assistant":
            logger.debug("Assistant: %s", message.content)
            if message.tool_calls:
                tool_calls_info = [{
                    "name": tc.get('function', {}).get('name'),
                    "arguments": tc.get('function', {}).get('arguments')
                } for tc in message.tool_calls]
                logger.debug("Tool Calls: %s", tool_calls_info)
        elif message.role == "tool":
            try:
                content = json.loads(message.content)
                if content.get("success"):
                    logger.debug("Tool (%s): Transcription successful", message.name)
                    logger.debug("Transcribed Text: %s", content.get("text"))
                    logger.debug("Details: %s", content.get("details"))
                else:
                    logger.error("Tool (%s): Error - %s", message.name, content.get("error", "Unknown error"))
            except json.JSONDecodeError:
                logger.debug("Tool (%s): %s", message.name, message.content)
    
    logger.debug("-" * 50)
    return processed_thread

async def main():
    try:
        # Run text-to-speech example
        logger.info("Running text-to-speech example...")
        thread = await text_to_speech_example()
        
        # Save the thread to ensure attachments are stored
        await thread_store.save(thread)
        logger.info(f"Thread saved with ID: {thread.id}")
        
        # Verify the thread can be retrieved with attachments
        retrieved_thread = await thread_store.get(thread.id)
        logger.info(f"Retrieved thread with ID: {retrieved_thread.id}")
        
        # Find the audio attachment
        audio_attachments = []
        for message in retrieved_thread.messages:
            for attachment in message.attachments:
                if attachment.mime_type and attachment.mime_type.startswith('audio/'):
                    audio_attachments.append(attachment)
        
        if audio_attachments:
            logger.info(f"Found {len(audio_attachments)} audio attachments in the thread")
            
            # Get the first audio attachment
            audio_attachment = audio_attachments[0]
            logger.info(f"Using audio file: {audio_attachment.filename} (ID: {audio_attachment.file_id})")
            
            # Get the content from the file store
            file_store = get_file_store()
            audio_bytes = await file_store.get(audio_attachment.file_id, audio_attachment.storage_path)
            
            # Save to a temporary file for the speech-to-text example
            output_dir = Path("./output")
            output_dir.mkdir(exist_ok=True)
            temp_audio_path = output_dir / audio_attachment.filename
            
            with open(temp_audio_path, "wb") as f:
                f.write(audio_bytes)
            
            # Run speech-to-text example with the retrieved audio
            logger.info("Running speech-to-text example with the retrieved audio...")
            await speech_to_text_example(temp_audio_path)
        else:
            logger.warning("No audio attachments found in the thread")
    except Exception as e:
        logger.error(f"Error in examples: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Exiting gracefully...")
        sys.exit(0) 