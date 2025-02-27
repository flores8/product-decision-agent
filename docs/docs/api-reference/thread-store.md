---
sidebar_position: 6
---

# ThreadStore API

The `ThreadStore` class provides a production-ready database implementation for thread storage. It supports both PostgreSQL and SQLite backends, with async operations and connection pooling.

## Initialization

```python
from tyler.database.thread_store import ThreadStore

# PostgreSQL
store = ThreadStore("postgresql+asyncpg://user:pass@localhost/dbname")
await store.initialize()  # Required before use

# SQLite
store = ThreadStore("sqlite+aiosqlite:///path/to/db.sqlite")
await store.initialize()

# Use with agent
agent = Agent(thread_store=store)
```

### Configuration

Environment variables:
```bash
TYLER_DB_ECHO=true          # Enable SQL logging
TYLER_DB_POOL_SIZE=10       # Connection pool size
TYLER_DB_MAX_OVERFLOW=20    # Max additional connections
```

## Methods

### initialize

Initialize the database connection and create schema.

```python
async def initialize(self) -> None
```

Must be called before using the store.

Example:
```python
store = ThreadStore("postgresql+asyncpg://...")
await store.initialize()
```

### save

Save a thread and its messages to the database.

```python
async def save(self, thread: Thread) -> Thread
```

Creates or updates thread and all messages. Returns saved thread.

Example:
```python
thread = Thread()
thread.add_message(Message(role="user", content="Hello"))
saved_thread = await store.save(thread)
```

### get

Get a thread by ID.

```python
async def get(self, thread_id: str) -> Optional[Thread]
```

Returns thread with all messages if found, None otherwise.

Example:
```python
thread = await store.get("thread_123")
if thread:
    print(f"Found {len(thread.messages)} messages")
```

### delete

Delete a thread and its messages.

```python
async def delete(self, thread_id: str) -> bool
```

Returns True if thread was deleted, False if not found.

Example:
```python
if await store.delete("thread_123"):
    print("Thread and messages deleted")
```

### list

List threads with pagination.

```python
async def list(
    self,
    limit: int = 100,
    offset: int = 0
) -> List[Thread]
```

Returns threads sorted by updated_at/created_at.

Example:
```python
# Get first page
threads = await store.list(limit=50, offset=0)

# Get next page
next_page = await store.list(limit=50, offset=50)
```

### find_by_attributes

Find threads by matching attributes.

```python
async def find_by_attributes(
    self,
    attributes: Dict[str, Any]
) -> List[Thread]
```

Returns threads where all specified attributes match.

Example:
```python
threads = await store.find_by_attributes({
    "customer_id": "123",
    "priority": "high"
})
```

### find_by_source

Find threads by source name and properties.

```python
async def find_by_source(
    self,
    source_name: str,
    properties: Dict[str, Any]
) -> List[Thread]
```

Returns threads matching source name and properties.

Example:
```python
threads = await store.find_by_source(
    "slack",
    {
        "channel": "C123",
        "thread_ts": "1234567890.123"
    }
)
```

### list_recent

List recent threads.

```python
async def list_recent(
    self,
    limit: Optional[int] = None
) -> List[Thread]
```

Returns threads sorted by updated_at/created_at (newest first).

Example:
```python
# Get 10 most recent threads
recent = await store.list_recent(limit=10)
```

### add_message

Add a message to a thread.

```python
async def add_message(
    self,
    thread_id: str,
    message: Message
) -> None
```

Adds message to thread and saves to database.

Example:
```python
message = Message(role="user", content="Hello")
await store.add_message("thread_123", message)
```

### get_messages

Get all messages for a thread.

```python
async def get_messages(
    self,
    thread_id: str
) -> List[Message]
```

Returns thread messages or empty list if thread not found.

Example:
```python
messages = await store.get_messages("thread_123")
for msg in messages:
    print(f"{msg.role}: {msg.content}")
```

## Best Practices

1. **Initialization**
   ```python
   # Always initialize before use
   store = ThreadStore(db_url)
   await store.initialize()
   
   # Use in context manager for cleanup
   async with store:
       thread = await store.get(thread_id)
   ```

2. **Connection Management**
   ```python
   # Configure pool size based on load
   os.environ["TYLER_DB_POOL_SIZE"] = "20"
   os.environ["TYLER_DB_MAX_OVERFLOW"] = "30"
   ```

3. **Error Handling**
   ```python
   try:
       thread = await store.get(thread_id)
   except Exception as e:
       print(f"Database error: {e}")
       # Handle error appropriately
   ```

4. **Batch Operations**
   ```python
   # Use pagination for large datasets
   async def process_all_threads():
       offset = 0
       while True:
           threads = await store.list(limit=100, offset=offset)
           if not threads:
               break
           for thread in threads:
               await process_thread(thread)
           offset += 100
   ```

5. **Source Management**
   ```python
   # Track external sources
   thread = Thread(
       source={
           "name": "slack",
           "channel": "C123",
           "thread_ts": "123.456"
       }
   )
   await store.save(thread)
   
   # Find related threads
   related = await store.find_by_source(
       "slack",
       {"channel": "C123"}
   )
   ```

## See Also

- [Thread API](./thread.md)
- [Message API](./message.md)
- [MemoryStore API](./memory-store.md) 