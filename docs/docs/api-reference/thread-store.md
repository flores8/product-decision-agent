---
sidebar_position: 6
---

# ThreadStore API

The `ThreadStore` class provides a unified interface for thread storage with pluggable backends. It supports both in-memory storage for development/testing and SQL backends (PostgreSQL and SQLite) for production use.

## Initialization

```python
from tyler.database.thread_store import ThreadStore

# In-memory storage (default when no configuration is provided)
store = ThreadStore()

# Environment variable configuration
# Set TYLER_DB_TYPE to 'postgresql' or 'sqlite'
# For PostgreSQL, also set TYLER_DB_HOST, TYLER_DB_PORT, TYLER_DB_NAME, TYLER_DB_USER, TYLER_DB_PASSWORD
# For SQLite, also set TYLER_DB_PATH
store = ThreadStore()

# Explicit PostgreSQL configuration
store = ThreadStore("postgresql+asyncpg://user:pass@localhost/dbname")

# Explicit SQLite configuration
store = ThreadStore("sqlite+aiosqlite:///path/to/db.sqlite")

# Use with agent
agent = Agent(thread_store=store)
```

### Configuration

Environment variables:
```bash
# Database type
TYLER_DB_TYPE=postgresql    # Use PostgreSQL backend
TYLER_DB_TYPE=sqlite        # Use SQLite backend

# PostgreSQL configuration (required when TYLER_DB_TYPE=postgresql)
TYLER_DB_HOST=localhost     # Database host
TYLER_DB_PORT=5432          # Database port
TYLER_DB_NAME=tyler         # Database name
TYLER_DB_USER=tyler_user    # Database user
TYLER_DB_PASSWORD=password  # Database password

# SQLite configuration (required when TYLER_DB_TYPE=sqlite)
TYLER_DB_PATH=/path/to/db.sqlite  # Path to SQLite database file

# Optional settings
TYLER_DB_ECHO=true          # Enable SQL logging
TYLER_DB_POOL_SIZE=10       # Connection pool size
TYLER_DB_MAX_OVERFLOW=20    # Max additional connections
```

## Methods

### initialize

Initialize the storage backend.

```python
async def initialize(self) -> None
```

This method is called automatically when needed, so you typically don't need to call it explicitly. It's available for cases where you want more control over initialization timing.

Example:
```python
# Explicit initialization (rarely needed)
store = ThreadStore("postgresql+asyncpg://...")
await store.initialize()
```

### save

Save a thread to storage.

```python
async def save(self, thread: Thread) -> Thread
```

Creates or updates thread and all messages. Returns saved thread. Automatically initializes the storage backend if needed.

Example:
```python
thread = Thread()
thread.add_message(Message(role="user", content="Hello"))
saved_thread = await store.save(thread)  # Initializes automatically if needed
```

### get

Get a thread by ID.

```python
async def get(self, thread_id: str) -> Optional[Thread]
```

Returns thread with all messages if found, None otherwise. Automatically initializes the storage backend if needed.

Example:
```python
thread = await store.get("thread_123")  # Initializes automatically if needed
if thread:
    print(f"Found {len(thread.messages)} messages")
```

### delete

Delete a thread by ID.

```python
async def delete(self, thread_id: str) -> bool
```

Returns True if thread was deleted, False if not found. Automatically initializes the storage backend if needed.

Example:
```python
if await store.delete("thread_123"):  # Initializes automatically if needed
    print("Thread deleted")
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

Returns threads sorted by updated_at/created_at. Automatically initializes the storage backend if needed.

Example:
```python
# Get first page (initializes automatically if needed)
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

Returns threads where all specified attributes match. Automatically initializes the storage backend if needed.

Example:
```python
# Initializes automatically if needed
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

Returns threads matching source name and properties. Automatically initializes the storage backend if needed.

Example:
```python
# Initializes automatically if needed
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

Returns threads sorted by updated_at/created_at (newest first). Automatically initializes the storage backend if needed.

Example:
```python
# Get 10 most recent threads (initializes automatically if needed)
recent = await store.list_recent(limit=10)
```

## Properties

### database_url

Get the database URL if using SQL backend.

```python
@property
def database_url(self) -> Optional[str]
```

Returns the database URL or None for memory backend.

### engine

Get the SQLAlchemy engine if using SQL backend.

```python
@property
def engine(self) -> Optional[Any]
```

Returns the SQLAlchemy engine or None for memory backend.

### async_session

Get the SQLAlchemy async session factory if using SQL backend.

```python
@property
def async_session(self) -> Optional[Any]
```

Returns the SQLAlchemy async session factory or None for memory backend.

## Backend Types

### MemoryBackend

In-memory storage for development and testing.

```python
# Uses memory backend by default when no configuration is provided
store = ThreadStore()
```

### SQLBackend

SQL-based storage for production use.

```python
# PostgreSQL
store = ThreadStore("postgresql+asyncpg://user:pass@localhost/dbname")

# SQLite
store = ThreadStore("sqlite+aiosqlite:///path/to/db.sqlite")
```

## Best Practices

1. **Lazy Initialization**
   ```python
   # Let ThreadStore initialize automatically (recommended)
   store = ThreadStore(db_url)
   thread = await store.get(thread_id)  # Initializes automatically
   
   # Explicit initialization (only if you need control over timing)
   store = ThreadStore(db_url)
   await store.initialize()
   ```

2. **Backend Selection**
   ```python
   # For development/testing
   store = ThreadStore()  # In-memory
   
   # For local development with persistence
   store = ThreadStore("sqlite+aiosqlite:///app.db")
   
   # For production
   store = ThreadStore("postgresql+asyncpg://user:pass@host/dbname")
   
   # Using environment variables
   # Set TYLER_DB_TYPE and other required variables
   store = ThreadStore()
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
   await store.save(thread)  # Initializes automatically if needed
   
   # Find related threads
   related = await store.find_by_source(
       "slack",
       {"channel": "C123"}
   )
   ```

6. **Attachment Processing**
   ```python
   # Attachments are automatically processed when saving a thread
   message = Message(role="user", content="Here's a file")
   message.add_attachment(file_bytes, filename="document.pdf")
   thread.add_message(message)
   
   # Save will process and store all attachments
   await store.save(thread)  # Initializes automatically if needed
   ```

7. **Environment Variable Configuration**
   ```python
   # Set required environment variables
   os.environ["TYLER_DB_TYPE"] = "postgresql"
   os.environ["TYLER_DB_HOST"] = "localhost"
   os.environ["TYLER_DB_PORT"] = "5432"
   os.environ["TYLER_DB_NAME"] = "tyler"
   os.environ["TYLER_DB_USER"] = "tyler_user"
   os.environ["TYLER_DB_PASSWORD"] = "password"
   
   # Create store using environment variables
   store = ThreadStore()  # Will use PostgreSQL with the configured settings
   ```

## See Also

- [Thread API](./thread.md)
- [Message API](./message.md)
- [Attachment API](./attachment.md) 