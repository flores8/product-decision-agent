from dotenv import load_dotenv
import os
import asyncio
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message
from tyler.database.thread_store import ThreadStore

# Load environment variables from .env file
load_dotenv()

def get_database_url(db_type="postgres"):
    """Helper function to get database URL based on type"""
    if db_type == "postgres":
        return "postgresql://tyler:tyler_dev@localhost/tyler"
    else:  # sqlite
        data_dir = os.path.expanduser("~/.tyler/data")
        os.makedirs(data_dir, exist_ok=True)
        return f"sqlite:///{data_dir}/tyler.db"

async def example_basic_persistence():
    """
    Demonstrates basic database persistence.
    Unlike memory storage, data persists between program runs.
    """
    print("\n=== Basic Persistence Example ===")
    
    # Initialize database store
    store = ThreadStore(get_database_url())
    
    # Create agent with database storage
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions",
        thread_store=store
    )
    
    # Create and save a new thread
    thread = Thread()
    store.save_thread(thread)  # Required with database storage
    thread_id = thread.id
    
    # Add a message
    message = Message(
        role="user",
        content="What are the benefits of database storage over memory storage?"
    )
    thread.add_message(message)
    store.save_thread(thread)  # Must save after changes
    
    # Get response - with database storage, we use thread ID
    processed_thread, new_messages = await agent.go(thread_id)
    
    print("Assistant's response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)
    
    print(f"\nThread saved in database with ID: {thread_id}")
    print("This thread will persist even after the program exits")
    print("You can find it in the database at:", store.database_url)

async def example_cross_session():
    """
    Demonstrates how database storage enables cross-session persistence.
    This is the key advantage over memory storage.
    """
    print("\n=== Cross-Session Example ===")
    
    # First session - creates and stores a conversation
    print("Session 1 (first program run):")
    store1 = ThreadStore(get_database_url())
    agent1 = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions",
        thread_store=store1
    )
    
    # Create thread in first session
    thread = Thread()
    store1.save_thread(thread)
    thread_id = thread.id
    
    message = Message(
        role="user",
        content="How does database persistence work?"
    )
    thread.add_message(message)
    store1.save_thread(thread)
    
    processed_thread, new_messages = await agent1.go(thread_id)
    print("First session response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)
    
    print("\nSession ends - program exits")
    print("Thread is safely stored in database")
    
    # Simulate new session - as if starting a new program
    print("\nSession 2 (new program run):")
    store2 = ThreadStore(get_database_url())
    agent2 = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions",
        thread_store=store2
    )
    
    # Retrieve thread from database
    thread = store2.get_thread(thread_id)
    print(f"Successfully retrieved thread {thread_id} from database")
    
    # Continue the conversation
    message = Message(
        role="user",
        content="Can you give an example of when this is useful?"
    )
    thread.add_message(message)
    store2.save_thread(thread)
    
    processed_thread, new_messages = await agent2.go(thread_id)
    print("\nSecond session response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)

async def example_sqlite_usage():
    """
    Demonstrates SQLite as a lightweight database option.
    Provides persistence without need for a database server.
    """
    print("\n=== SQLite Example ===")
    
    # Initialize SQLite store
    store = ThreadStore(get_database_url("sqlite"))
    print("Using SQLite database at:", store.database_url)
    
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions",
        thread_store=store
    )
    
    # Create and save thread
    thread = Thread()
    store.save_thread(thread)
    
    message = Message(
        role="user",
        content="When should I use SQLite instead of PostgreSQL?"
    )
    thread.add_message(message)
    store.save_thread(thread)
    
    processed_thread, new_messages = await agent.go(thread.id)
    
    print("Assistant's response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)
    
    print("\nKey differences from PostgreSQL:")
    print("- File-based: no server needed")
    print("- Great for development and testing")
    print("- Perfect for single-user applications")
    print("- Still provides persistence unlike memory storage")

async def main():
    # Run all examples
    await example_basic_persistence()
    await example_cross_session()
    await example_sqlite_usage()

if __name__ == "__main__":
    asyncio.run(main()) 