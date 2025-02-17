#!/usr/bin/env python3

from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
import asyncio
import weave
import os
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging based on LOG_LEVEL environment variable
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Set log level for all tyler loggers
for logger_name in ['tyler', 'tyler.models.agent', 'tyler.utils.tool_runner', '__main__']:
    logging.getLogger(logger_name).setLevel(log_level)

try:
    if os.getenv("WANDB_API_KEY"):
        weave.init("tyler")
        logger.info("Weave tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize weave tracing: {e}. Continuing without weave.")

def custom_calculator_implementation(operation: str, x: float, y: float) -> str:
    """
    Implementation of a simple calculator tool.
    """
    try:
        if operation == "add":
            result = x + y
        elif operation == "subtract":
            result = x - y
        elif operation == "multiply":
            result = x * y
        elif operation == "divide":
            if y == 0:
                return "Error: Division by zero"
            result = x / y
        else:
            return f"Error: Unknown operation {operation}"
        
        return f"Result of {operation}({x}, {y}) = {result}"
    except Exception as e:
        return f"Error performing calculation: {str(e)}"

# Define custom calculator tool
custom_calculator_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform basic mathematical operations",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The mathematical operation to perform (add, subtract, multiply, divide)",
                        "enum": ["add", "subtract", "multiply", "divide"]
                    },
                    "x": {
                        "type": "number",
                        "description": "First number"
                    },
                    "y": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["operation", "x", "y"]
            }
        }
    },
    "implementation": custom_calculator_implementation,
    "attributes": {
        "category": "math",
        "version": "1.0"
    }
}

# Initialize the agent with both built-in and custom tools
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with calculations and web searches",
    tools=[
        "web",                    # Load the web tools module
        custom_calculator_tool,   # Add our calculator tool
    ]
)

async def main():
    # Create a thread
    thread = Thread()

    # Example conversation with calculations and web searches
    conversations = [
        "What is 25 multiplied by 13?",
        "Now divide that result by 5."
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
            elif message.role == "tool":
                print(f"\nTool ({message.name}): {message.content}")
        
        print("\n" + "-"*50)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
        sys.exit(0) 