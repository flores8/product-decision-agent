from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message
from tyler.database.thread_store import ThreadStore
import asyncio
import weave
import os

# Load environment variables from .env file
load_dotenv()

# Initialize weave for tracing (optional - requires WANDB_API_KEY environment variable)
if os.getenv("WANDB_API_KEY"):
    weave.init("tyler")

# Initialize the thread store
thread_store = ThreadStore()

# Initialize a highly customized agent
agent = Agent(
    model_name="gpt-4o",
    temperature=0.2,  # Lower temperature for more focused responses
    name="DataWizard",  # Custom name
    purpose="To analyze data and provide insights with a focus on accuracy",
    notes="""
    - Always provide statistical context when analyzing data
    - Use precise numerical values when possible
    - Cite sources when making factual claims
    - Break down complex analyses into steps
    """,
    tools=["web"],  # Using the web tools module
    thread_store=thread_store
)

async def main():
    # Create a new thread
    thread = Thread()
    await thread_store.save(thread)

    # Add a user message
    message = Message(
        role="user",
        content="What were the top 3 cryptocurrencies by market cap in today?"
    )
    thread.add_message(message)
    await thread_store.save(thread)

    # Process the thread
    processed_thread, new_messages = await agent.go(thread.id)

    # Print the assistant's response
    for message in new_messages:
        if message.role == "assistant":
            print(f"{agent.name}: {message.content}")

if __name__ == "__main__":
    asyncio.run(main()) 