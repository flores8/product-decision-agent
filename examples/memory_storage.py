from dotenv import load_dotenv
import asyncio
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message
from tyler.database.memory_store import MemoryThreadStore

# Load environment variables from .env file
load_dotenv()

async def example_default_memory_storage():
    """
    Demonstrates using the default in-memory storage.
    This is the simplest way to use Tyler - no configuration needed.
    Memory is cleared when the program exits.
    """
    print("\n=== Default Memory Storage Example ===")
    
    # Create agent - uses MemoryThreadStore by default
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions"
    )
    
    # Create thread and add message
    thread = Thread()
    message = Message(
        role="user",
        content="What's the best way to learn Python?"
    )
    thread.add_message(message)
    
    # Get response - with memory storage, we pass the Thread object directly
    processed_thread, new_messages = await agent.go(thread)
    
    print("Assistant's response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)
            
    print("\nThread exists in memory with ID:", thread.id)
    print("Note: This thread will be lost when the program exits")

async def example_explicit_memory_store():
    """
    Demonstrates explicitly creating and using a MemoryThreadStore.
    Shows how to work with the store directly.
    """
    print("\n=== Explicit Memory Store Example ===")
    
    # Create memory store and agent
    store = MemoryThreadStore()
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions",
        thread_store=store
    )
    
    # Create and save thread
    thread = Thread()
    store.save_thread(thread)  # Optional with memory store
    
    # Add message
    message = Message(
        role="user",
        content="Explain the difference between memory and database storage."
    )
    thread.add_message(message)
    
    # Get response - can use either thread or thread.id
    processed_thread, new_messages = await agent.go(thread)  # or thread.id
    
    print("Assistant's response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)
    
    # Demonstrate store operations
    print("\nMemory Store Operations:")
    print(f"- Thread count: {len(store.list_threads())}")
    print(f"- Can get thread by ID: {store.get_thread(thread.id) is not None}")
    print(f"- Thread messages: {len(store.get_messages(thread.id))}")

async def example_multiple_conversations():
    """
    Demonstrates managing multiple conversations in memory.
    Shows how threads are independent and exist only in memory.
    """
    print("\n=== Multiple Conversations Example ===")
    
    store = MemoryThreadStore()
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help with general questions",
        thread_store=store
    )
    
    # Create multiple threads
    threads = []
    questions = [
        "What is a Python decorator?",
        "How do Python generators work?",
        "Explain Python context managers."
    ]
    
    # Start multiple conversations
    for question in questions:
        thread = Thread()
        store.save_thread(thread)
        threads.append(thread)
        
        message = Message(role="user", content=question)
        thread.add_message(message)
        
        print(f"\nQuestion: {question}")
        processed_thread, new_messages = await agent.go(thread)
        
        for message in new_messages:
            if message.role == "assistant":
                print("Answer:", message.content[:100] + "...")
    
    print("\nMemory Store State:")
    print(f"- Active threads: {len(store.list_threads())}")
    print("- Thread IDs:", [t.id for t in threads])
    print("Note: All these conversations exist only in memory")

async def main():
    # Run all examples
    await example_default_memory_storage()
    await example_explicit_memory_store()
    await example_multiple_conversations()

if __name__ == "__main__":
    asyncio.run(main()) 