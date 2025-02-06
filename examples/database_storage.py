from dotenv import load_dotenv
import os
import asyncio
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message
from tyler.database.thread_store import ThreadStore
import weave

# Load environment variables from .env file
load_dotenv()

# Initialize weave for tracing (optional - requires WANDB_API_KEY environment variable)
if os.getenv("WANDB_API_KEY"):
    weave.init("tyler")

def get_database_url(db_type="postgres"):
    """Helper function to get database URL based on type"""
    if db_type == "postgres":
        return "postgresql+asyncpg://tyler:tyler_dev@localhost/tyler"
    else:  # sqlite
        data_dir = os.path.expanduser("~/.tyler/data")
        os.makedirs(data_dir, exist_ok=True)
        return f"sqlite+aiosqlite:///{data_dir}/tyler.db"

async def example_basic_persistence():
    """
    Demonstrates basic database persistence with metrics tracking.
    Unlike memory storage, data persists between program runs.
    """
    print("\n=== Basic Persistence Example ===")
    
    # Initialize database store
    store = ThreadStore(get_database_url())
    await store.initialize()  # Required to create tables
    
    # Create agent with database storage
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions",
        thread_store=store
    )
    
    # Create and save a new thread
    thread = Thread()
    await store.save(thread)  # Required with database storage
    thread_id = thread.id
    
    # Add a message
    message = Message(
        role="user",
        content="What are the benefits of database storage over memory storage?"
    )
    thread.add_message(message)
    await store.save(thread)  # Must save after changes
    
    # Get response - with database storage, we use thread ID
    processed_thread, new_messages = await agent.go(thread_id)
    
    print("Assistant's response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)
            print("\nMessage metrics:")
            print(f"- Tokens: {message.metrics['completion_tokens']} completion, {message.metrics['prompt_tokens']} prompt")
            print(f"- Model: {message.metrics['model']}")
            print(f"- Latency: {message.metrics['latency']:.0f}ms")
    
    print(f"\nThread metrics:")
    print(f"- Total tokens: {processed_thread.metrics['total_tokens']}")
    for model, usage in processed_thread.metrics['model_usage'].items():
        print(f"- {model}: {usage['calls']} calls, {usage['total_tokens']} tokens")
    
    print(f"\nThread saved in database with ID: {thread_id}")
    print("This thread will persist even after the program exits")
    print("You can find it in the database at:", store.database_url)

async def example_cross_session():
    """
    Demonstrates how database storage enables cross-session persistence
    with metrics tracking across sessions.
    """
    print("\n=== Cross-Session Example ===")
    
    # First session - creates and stores a conversation
    print("Session 1 (first program run):")
    store1 = ThreadStore(get_database_url())
    await store1.initialize()
    
    agent1 = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions",
        thread_store=store1
    )
    
    # Create thread in first session
    thread = Thread()
    await store1.save(thread)
    thread_id = thread.id
    
    message = Message(
        role="user",
        content="How does database persistence work?"
    )
    thread.add_message(message)
    await store1.save(thread)
    
    processed_thread, new_messages = await agent1.go(thread_id)
    print("First session response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)
    
    print("\nFirst session metrics:")
    print(f"- Total tokens: {processed_thread.metrics['total_tokens']}")
    
    print("\nSession ends - program exits")
    print("Thread and metrics are safely stored in database")
    
    # Simulate new session - as if starting a new program
    print("\nSession 2 (new program run):")
    store2 = ThreadStore(get_database_url())
    await store2.initialize()
    
    agent2 = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions",
        thread_store=store2
    )
    
    # Retrieve thread from database
    thread = await store2.get(thread_id)
    print(f"Successfully retrieved thread {thread_id} from database")
    print(f"Previous session tokens: {thread.metrics['total_tokens']}")
    
    # Continue the conversation
    message = Message(
        role="user",
        content="Can you give an example of when this is useful?"
    )
    thread.add_message(message)
    await store2.save(thread)
    
    processed_thread, new_messages = await agent2.go(thread_id)
    print("\nSecond session response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)
    
    print("\nCumulative metrics across both sessions:")
    print(f"- Total tokens: {processed_thread.metrics['total_tokens']}")
    for model, usage in processed_thread.metrics['model_usage'].items():
        print(f"- {model}: {usage['calls']} calls, {usage['total_tokens']} tokens")

async def example_sqlite_usage():
    """
    Demonstrates SQLite as a lightweight database option
    with full metrics support.
    """
    print("\n=== SQLite Example ===")
    
    # Initialize SQLite store
    store = ThreadStore(get_database_url("sqlite"))
    await store.initialize()
    print("Using SQLite database at:", store.database_url)
    
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions",
        thread_store=store
    )
    
    # Create and save thread
    thread = Thread()
    await store.save(thread)
    
    message = Message(
        role="user",
        content="When should I use SQLite instead of PostgreSQL?"
    )
    thread.add_message(message)
    await store.save(thread)
    
    processed_thread, new_messages = await agent.go(thread.id)
    
    print("Assistant's response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)
            print(f"\nResponse metrics:")
            print(f"- Tokens: {message.metrics['completion_tokens']} completion")
            print(f"- Latency: {message.metrics['latency']:.0f}ms")
    
    print("\nKey differences from PostgreSQL:")
    print("- File-based: no server needed")
    print("- Great for development and testing")
    print("- Perfect for single-user applications")
    print("- Still provides full metrics tracking")
    print("- Messages stored in separate table")

async def example_metrics_query():
    """
    Demonstrates how to query and analyze metrics across threads.
    """
    print("\n=== Metrics Query Example ===")
    
    store = ThreadStore(get_database_url())
    await store.initialize()
    
    # List recent threads with their metrics
    threads = await store.list_recent(limit=5)
    
    total_tokens = sum(t.metrics['total_tokens'] for t in threads)
    print(f"\nTotal tokens used across {len(threads)} recent threads: {total_tokens}")
    
    # Aggregate model usage
    model_usage = {}
    for thread in threads:
        for model, usage in thread.metrics['model_usage'].items():
            if model not in model_usage:
                model_usage[model] = {"calls": 0, "tokens": 0}
            model_usage[model]["calls"] += usage['calls']
            model_usage[model]["tokens"] += usage['total_tokens']
    
    print("\nModel usage summary:")
    for model, usage in model_usage.items():
        print(f"- {model}: {usage['calls']} calls, {usage['tokens']} tokens")

async def main():
    # Run all examples
    await example_basic_persistence()
    await example_cross_session()
    await example_sqlite_usage()
    await example_metrics_query()  # New example for metrics

if __name__ == "__main__":
    asyncio.run(main()) 