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

# Initialize the agent with streaming enabled
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with translations and web searches",
    tools=[
        "web",                     # Load the web tools module
        custom_translator_tool,    # Add our translator tool
    ],
    temperature=0.7,
    stream=True  # Enable streaming responses
)

async def main():
    # Example conversation with translations and web searches using real streaming
    conversations = [
        "How do you say 'hello' in Spanish?",
        "Now translate 'good morning' to French."
    ]

    for user_input in conversations:
        print(f"\nUser: {user_input}")

        # Create a new thread for each conversation
        thread = Thread()
        message = Message(role="user", content=user_input)
        thread.add_message(message)

        # Build completion parameters with streaming enabled
        completion_params = {
            "model": agent.model_name,
            "messages": thread.get_messages_for_chat_completion(),
            "temperature": agent.temperature,
            "stream": True
        }
        if agent._processed_tools:
            completion_params["tools"] = agent._processed_tools

        # Get the streaming response directly from the agent
        streaming_response, call = await agent._get_completion.call(agent, **completion_params)

        print("\nAssistant (streaming): ", end='', flush=True)
        async for chunk in streaming_response:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content is not None:
                print(delta.content, end='', flush=True)
        print("\n" + "-" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
        sys.exit(0) 