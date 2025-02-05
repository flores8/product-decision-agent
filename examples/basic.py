from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message
import asyncio
import weave
import os

# Load environment variables from .env file
load_dotenv()

# Initialize weave for tracing (optional - requires WANDB_API_KEY environment variable)
if os.getenv("WANDB_API_KEY"):
    weave.init("tyler")

# Initialize the agent (uses in-memory storage by default)
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with general questions"
)

async def main():
    # Create a new thread
    thread = Thread()

    # Add a user message
    message = Message(
        role="user",
        content="What is the distance between Earth and Moon?"
    )
    thread.add_message(message)

    # Process the thread
    # Since we're using in-memory storage, we can pass the Thread object directly
    processed_thread, new_messages = await agent.go(thread)

    # Print the assistant's response
    for message in new_messages:
        if message.role == "assistant":
            print(f"Assistant: {message.content}")

    # Add another message to continue the conversation
    message = Message(
        role="user",
        content="How long would it take to travel that distance in a spacecraft?"
    )
    thread.add_message(message)

    # Continue the conversation
    processed_thread, new_messages = await agent.go(thread)

    # Print the assistant's response
    for message in new_messages:
        if message.role == "assistant":
            print(f"Assistant: {message.content}")

if __name__ == "__main__":
    asyncio.run(main()) 