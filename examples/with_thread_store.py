from dotenv import load_dotenv
import os
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message
from tyler.database.thread_store import ThreadStore
import asyncio

# Load environment variables from .env file
load_dotenv()

# Initialize the thread store
thread_store = ThreadStore()

# Initialize the agent with thread store
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with data analysis and general questions",
    notes="Custom notes about the agent's behavior",
    temperature=0.7,
    thread_store=thread_store
)

async def main():
    # Create a new thread
    thread = Thread()
    thread_store.save(thread)  # Save the thread before using it

    # Add a user message
    message = Message(
        role="user",
        content="Who has walked on the moon?"
    )
    thread.add_message(message)
    thread_store.save(thread)

    # Process the thread using thread ID
    processed_thread, new_messages = await agent.go(thread.id)

    # Print the assistant's response
    for message in new_messages:
        if message.role == "assistant":
            print(f"Assistant: {message.content}")

    # You can later retrieve and continue the conversation using the thread ID
    continued_thread, more_messages = await agent.go(thread.id)

if __name__ == "__main__":
    asyncio.run(main()) 