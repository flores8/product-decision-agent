---
sidebar_position: 5
---

# Database Storage

This example demonstrates how to use persistent database storage with Tyler, including PostgreSQL integration and metrics tracking.

## Overview

The example shows:
- Setting up PostgreSQL database storage
- Initializing and using ThreadStore
- Saving and retrieving threads
- Tracking message metrics
- Using file storage

## Code

```python
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

# Initialize weave for tracing (optional)
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
```

## Step-by-Step Explanation

### 1. Database Setup
```python
db_url = f"postgresql+asyncpg://{os.getenv('TYLER_DB_USER')}:{os.getenv('TYLER_DB_PASSWORD')}@{os.getenv('TYLER_DB_HOST')}:{os.getenv('TYLER_DB_PORT')}/{os.getenv('TYLER_DB_NAME')}"

store = ThreadStore(db_url)
await store.initialize()
```
- Constructs database URL from environment variables
- Initializes ThreadStore with PostgreSQL
- Creates necessary database tables

### 2. File Storage Setup
```python
file_store = get_file_store()
print(f"Initialized file store at: {file_store.base_path}")
```
- Initializes file storage for attachments
- Uses default or configured storage path

### 3. Agent Configuration
```python
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with general questions",
    thread_store=store
)
```
- Creates agent with database storage
- Sets model and purpose
- Connects to thread store

### 4. Thread Management
```python
thread = Thread()
await store.save(thread)

message = Message(
    role="user",
    content="What are the benefits of database storage over memory storage?"
)
thread.add_message(message)
await store.save(thread)
```
- Creates and saves threads
- Adds messages
- Persists changes to database

## Configuration Requirements

### Environment Variables
```bash
# Database Configuration
TYLER_DB_TYPE=postgresql
TYLER_DB_HOST=localhost
TYLER_DB_PORT=5432
TYLER_DB_NAME=tyler
TYLER_DB_USER=tyler
TYLER_DB_PASSWORD=tyler_dev

# Optional Database Settings
TYLER_DB_ECHO=false
TYLER_DB_POOL_SIZE=5
TYLER_DB_MAX_OVERFLOW=10
TYLER_DB_POOL_TIMEOUT=30
TYLER_DB_POOL_RECYCLE=1800

# File Storage Configuration
TYLER_FILE_STORAGE_TYPE=local
TYLER_FILE_STORAGE_PATH=/path/to/files

# Monitoring
WANDB_API_KEY=your-wandb-api-key
```

## Expected Output

When you run this example, you'll see output similar to:

```
Initialized file store at: /Users/username/.tyler/files

Assistant's response:
Database storage offers several advantages over in-memory storage:
1. Persistence across sessions
2. Scalability for large datasets
3. Concurrent access support
4. Data integrity and recovery
5. Query and filtering capabilities

Message metrics:
- Tokens: 128 completion, 84 prompt
- Model: gpt-4o
- Latency: 450ms
```

## Key Concepts

1. **Database Storage**
   - Thread persistence
   - Message history
   - Concurrent access
   - Data integrity

2. **File Storage**
   - Attachment handling
   - File organization
   - Path management

3. **Metrics Tracking**
   - Token usage
   - Model performance
   - Response latency

4. **Environment Configuration**
   - Database settings
   - Connection pooling
   - Storage paths

## Common Customizations

### SQLite Storage
```python
store = ThreadStore("sqlite:///path/to/database.db")
```

### Custom Pool Settings
```python
store = ThreadStore(
    url=db_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=60
)
```

### Custom File Storage
```python
from tyler.storage import FileStorage

store = FileStorage(
    storage_type="s3",
    bucket_name="my-bucket"
)
``` 