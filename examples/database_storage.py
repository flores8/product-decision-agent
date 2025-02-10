from dotenv import load_dotenv
import os
import asyncio
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message
from tyler.database.thread_store import ThreadStore
from tyler.storage import get_file_store
import weave

# Load environment variables from .env file
load_dotenv()

# Initialize weave for tracing (optional - requires WANDB_API_KEY environment variable)
if os.getenv("WANDB_API_KEY"):
    weave.init("tyler")

async def main():
    """
    Demonstrates database persistence with metrics tracking.
    Uses environment variables for database configuration.
    """
    # Construct PostgreSQL URL from environment variables
    db_url = f"postgresql+asyncpg://{os.getenv('TYLER_DB_USER')}:{os.getenv('TYLER_DB_PASSWORD')}@{os.getenv('TYLER_DB_HOST')}:{os.getenv('TYLER_DB_PORT')}/{os.getenv('TYLER_DB_NAME')}"

    # Initialize ThreadStore with PostgreSQL URL
    store = ThreadStore(db_url)
    await store.initialize()  # Required to create tables

    # Initialize file store
    file_store = get_file_store()
    print(f"Initialized file store at: {file_store.base_path}")
    
    # Create agent with database storage
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions",
        thread_store=store
    )
    
    # Create and save a new thread
    thread = Thread()
    await store.save(thread)
    
    # Add a message
    message = Message(
        role="user",
        content="What are the benefits of database storage over memory storage?"
    )
    thread.add_message(message)
    await store.save(thread)
    
    # Get response
    processed_thread, new_messages = await agent.go(thread)
    
    print("Assistant's response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)
            print("\nMessage metrics:")
            print(f"- Tokens: {message.metrics['completion_tokens']} completion, {message.metrics['prompt_tokens']} prompt")
            print(f"- Model: {message.metrics['model']}")
            print(f"- Latency: {message.metrics['latency']:.0f}ms")

if __name__ == "__main__":
    asyncio.run(main()) 