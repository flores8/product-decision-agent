#!/usr/bin/env python3

from dotenv import load_dotenv
from tyler.models.agent import Agent, StreamUpdate
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

try:
    if os.getenv("WANDB_API_KEY"):
        weave.init("tyler")
        logger.info("Weave tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize weave tracing: {e}. Continuing without weave.")

def custom_translator_implementation(text: str, target_language: str) -> str:
    """
    Implementation of a mock translator tool.
    In a real application, this would use a translation API.
    """
    # This is a mock implementation
    translations = {
        "spanish": {
            "hello": "hola",
            "world": "mundo",
            "how are you": "¿cómo estás?",
            "good morning": "buenos días"
        },
        "french": {
            "hello": "bonjour",
            "world": "monde",
            "how are you": "comment allez-vous?",
            "good morning": "bonjour"
        }
    }
    
    target_language = target_language.lower()
    text = text.lower()
    
    if target_language not in translations:
        return f"Error: Unsupported target language '{target_language}'"
        
    if text in translations[target_language]:
        return f"Translation: {translations[target_language][text]}"
    else:
        return f"Mock translation to {target_language}: [{text}]"

# Define custom translator tool
logger.debug("Defining custom translator tool...")
custom_translator_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "translate",
            "description": "Translate text to another language",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to translate"
                    },
                    "target_language": {
                        "type": "string",
                        "description": "The target language for translation",
                        "enum": ["Spanish", "French"]
                    }
                },
                "required": ["text", "target_language"]
            }
        }
    },
    "implementation": custom_translator_implementation,
    "attributes": {
        "category": "language",
        "version": "1.0"
    }
}
logger.debug(f"Custom translator tool definition: {custom_translator_tool}")

# Initialize the agent with streaming enabled
logger.debug("Initializing agent...")
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with translations and web searches",
    tools=[
        "web",                     # Load the web tools module
        custom_translator_tool,    # Add our translator tool
    ],
    temperature=0.7
)

async def main():
    # Example conversation with translations and web searches
    conversations = [
        "How do you say 'hello' in Spanish?",
        "Now translate 'good morning' to French."
    ]

    # Create a single thread for the entire conversation
    thread = Thread()

    for user_input in conversations:
        print(f"\nUser: {user_input}")

        # Add user message to thread
        message = Message(role="user", content=user_input)
        thread.add_message(message)

        print("\nAssistant: ", end='', flush=True)

        # Process the thread using go_stream
        async for update in agent.go_stream(thread):
            if update.type == StreamUpdate.Type.CONTENT_CHUNK:
                # Print content chunks as they arrive
                print(update.data, end='', flush=True)
            elif update.type == StreamUpdate.Type.TOOL_MESSAGE:
                # Print translation results on new lines
                tool_message = update.data
                print(f"\nTranslation: {tool_message.content}")
            elif update.type == StreamUpdate.Type.ERROR:
                # Print any errors that occur
                print(f"\nError: {update.data}")
            elif update.type == StreamUpdate.Type.COMPLETE:
                # Final update contains (thread, new_messages)
                print()  # Add newline after completion

        print("\n" + "-"*50)  # Separator between conversations

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
        sys.exit(0) 