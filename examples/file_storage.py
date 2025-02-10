from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.storage import init_file_store
import asyncio
import os
import weave

# Load environment variables from .env file
load_dotenv()

# Initialize weave for tracing (optional - requires WANDB_API_KEY environment variable)
if os.getenv("WANDB_API_KEY"):
    weave.init("tyler")

async def example_basic_file_storage():
    """
    Demonstrates basic file storage functionality with a PDF document.
    """
    print("\n=== Basic File Storage Example ===")
    
    # Initialize file storage with custom path (optional)
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "files")
    init_file_store('local', base_path=data_dir)
    
    # Create agent
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help analyze documents"
    )
    
    # Create thread with PDF attachment
    thread = Thread()
    
    # Path to example PDF in the repository
    pdf_path = os.path.join(os.path.dirname(__file__), "example.pdf")
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
    except FileNotFoundError:
        print(f"Note: Create {pdf_path} to test PDF processing")
        # Create a text file instead for the example
        pdf_content = b"This is example content for testing file storage."
        pdf_path = "example.txt"
    
    message = Message(
        role="user",
        content="Can you analyze this document?",
        file_content=pdf_content,
        filename=os.path.basename(pdf_path)
    )
    thread.add_message(message)
    
    # Process thread - file will be automatically stored
    processed_thread, new_messages = await agent.go(thread)
    
    print("\nAssistant's response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)

async def example_multiple_files():
    """
    Demonstrates handling multiple files in a single thread.
    """
    print("\n=== Multiple Files Example ===")
    
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help analyze multiple documents"
    )
    
    thread = Thread()
    
    # Add multiple text files for the example
    files = [
        ("report.txt", b"Q1 sales increased by 15%"),
        ("data.txt", b"Customer satisfaction: 4.5/5"),
        ("notes.txt", b"Team meeting scheduled for Friday")
    ]
    
    # Add each file in separate messages
    for filename, content in files:
        message = Message(
            role="user",
            content=f"Please analyze {filename}",
            file_content=content,
            filename=filename
        )
        thread.add_message(message)
    
    # Process thread with multiple files
    processed_thread, new_messages = await agent.go(thread)
    
    print("\nAssistant's response:")
    for message in new_messages:
        if message.role == "assistant":
            print(message.content)

async def example_file_organization():
    """
    Demonstrates the file organization structure.
    """
    print("\n=== File Organization Example ===")
    
    # Get the storage path
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "files")
    print(f"\nFile storage location: {data_dir}")
    print("\nFile organization structure:")
    print("- Files are stored in a sharded directory structure")
    print("- Each file gets a unique UUID")
    print("- Storage pattern: {base_path}/{uuid[:2]}/{uuid[2:]}")
    print("- Original filenames and metadata preserved in database")
    print("- Automatic directory creation as needed")
    
    # Create some example files to show structure
    init_file_store('local', base_path=data_dir)
    agent = Agent(model_name="gpt-4o")
    thread = Thread()
    
    message = Message(
        role="user",
        content="Here's a test file",
        file_content=b"Test content",
        filename="test.txt"
    )
    thread.add_message(message)
    
    # Process to trigger file storage
    await agent.go(thread)
    
    print("\nCheck the storage directory to see the structure!")

async def main():
    # Run all examples
    await example_basic_file_storage()
    await example_multiple_files()
    await example_file_organization()

if __name__ == "__main__":
    asyncio.run(main()) 