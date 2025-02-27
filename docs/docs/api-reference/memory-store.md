---
sidebar_position: 5
---

# MemoryStore API

The `MemoryThreadStore` class provides a simple in-memory implementation of thread storage using a Python dictionary. It's perfect for development, testing, and one-off scripts where persistence isn't required.

## Initialization

```python
from tyler.database.memory_store import MemoryThreadStore

# Create store
store = MemoryThreadStore()

# Use with agent
agent = Agent(thread_store=store)  # Optional, MemoryStore is default
```

## Methods

### save

Save a thread to memory.

```python
async def save(self, thread: Thread) -> Thread
```

Returns the saved thread. Thread is stored immediately in memory.

Example:
```python
thread = Thread()
saved_thread = await store.save(thread)
```

### get

Get a thread by ID.

```python
async def get(self, thread_id: str) -> Optional[Thread]
```

Returns the thread if found, None otherwise.

Example:
```python
thread = await store.get("thread_123")
if thread:
    print(f"Found thread: {thread.title}")
```

### delete

Delete a thread by ID.

```python
async def delete(self, thread_id: str) -> bool
```

Returns True if thread was deleted, False if not found.

Example:
```python
if await store.delete("thread_123"):
    print("Thread deleted")
else:
    print("Thread not found")
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

Returns threads sorted by updated_at (or created_at if no updates).

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
def add_message(
    self,
    thread_id: str,
    message: Message
) -> None
```

Adds message directly to thread if found.

Example:
```python
message = Message(role="user", content="Hello")
store.add_message("thread_123", message)
```

### get_messages

Get all messages for a thread.

```python
def get_messages(
    self,
    thread_id: str
) -> List[Message]
```

Returns thread messages or empty list if thread not found.

Example:
```python
messages = store.get_messages("thread_123")
for msg in messages:
    print(f"{msg.role}: {msg.content}")
```

## Best Practices

1. **Thread Creation**
   ```python
   # Create and save in one step
   thread = Thread()
   await store.save(thread)
   ```

2. **Message Management**
   ```python
   # Add messages through thread
   thread.add_message(message)
   await store.save(thread)  # Save changes
   
   # Or directly through store
   store.add_message(thread.id, message)
   ```

3. **Pagination**
   ```python
   # Use offset pagination for large lists
   page_size = 50
   page = 0
   
   while True:
       threads = await store.list(
           limit=page_size,
           offset=page * page_size
       )
       if not threads:
           break
       # Process threads
       page += 1
   ```

4. **Source Tracking**
   ```python
   # Find all Slack threads in channel
   slack_threads = await store.find_by_source(
       "slack",
       {"channel": "C123"}
   )
   ```

5. **Attribute Filtering**
   ```python
   # Find high priority customer threads
   priority_threads = await store.find_by_attributes({
       "priority": "high",
       "type": "customer"
   })
   ```

## See Also

- [Thread API](./thread.md)
- [Message API](./message.md)
- [ThreadStore API](./thread-store.md) 