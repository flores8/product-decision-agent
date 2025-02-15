---
sidebar_position: 5
---

# ThreadStore API

The `ThreadStore` class provides persistent storage for threads using SQLAlchemy, supporting both PostgreSQL and SQLite backends. It handles thread storage, retrieval, and management with automatic attachment handling.

## Initialization

```python
from tyler.database.thread_store import ThreadStore

store = ThreadStore(
    database_url: Optional[str] = None
)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `database_url` | Optional[str] | No | None | SQLAlchemy async database URL. If not provided, uses a temporary SQLite database |

### Database URL Examples

```python
# PostgreSQL for production
store = ThreadStore("postgresql+asyncpg://user:pass@localhost/dbname")

# SQLite for development
store = ThreadStore("sqlite+aiosqlite:///path/to/db.sqlite")

# In-memory SQLite (temporary)
store = ThreadStore(":memory:")

# Default (temporary SQLite in system temp directory)
store = ThreadStore()
```

## Methods

### initialize

Initialize the database by creating necessary tables.

```python
async def initialize(self) -> None
```

#### Example

```python
store = ThreadStore()
await store.initialize()  # Must call this before using
```

### save

Save a thread and its messages to the database. Automatically handles attachment storage.

```python
async def save(self, thread: Thread) -> Thread
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread` | Thread | Yes | Thread object to save |

#### Returns

| Type | Description |
|------|-------------|
| Thread | The saved thread object |

#### Raises

| Exception | Description |
|-----------|-------------|
| RuntimeError | If thread save fails or attachment storage fails |

#### Example

```python
thread = Thread()
message = Message(content="Hello with attachment", attachments=[attachment])
thread.add_message(message)
await store.save(thread)  # Automatically stores attachments
```

### get

Retrieve a thread by its ID.

```python
async def get(self, thread_id: str) -> Optional[Thread]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | str | Yes | ID of the thread to retrieve |

#### Returns

| Type | Description |
|------|-------------|
| Optional[Thread] | The thread if found, None otherwise |

#### Example

```python
thread = await store.get("thread_123")
if thread:
    print(f"Found thread: {thread.title}")
```

### list

List threads with pagination.

```python
async def list(self, limit: int = 100, offset: int = 0) -> List[Thread]
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | int | No | 100 | Maximum number of threads to return |
| `offset` | int | No | 0 | Number of threads to skip |

#### Returns

| Type | Description |
|------|-------------|
| List[Thread] | List of threads |

#### Example

```python
# Get first page of threads
threads = await store.list(limit=10)

# Get next page
next_page = await store.list(limit=10, offset=10)
```

### list_recent

List recent threads ordered by last update.

```python
async def list_recent(self, limit: int = 30) -> List[Thread]
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | int | No | 30 | Maximum number of threads to return |

#### Returns

| Type | Description |
|------|-------------|
| List[Thread] | List of recent threads |

#### Example

```python
recent_threads = await store.list_recent(limit=5)
```

### find_by_attributes

Find threads by matching attributes.

```python
async def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `attributes` | Dict[str, Any] | Yes | Attributes to match against |

#### Returns

| Type | Description |
|------|-------------|
| List[Thread] | List of matching threads |

#### Example

```python
# Find threads with specific attributes
threads = await store.find_by_attributes({
    "category": "support",
    "priority": "high"
})
```

### find_by_source

Find threads by source name and properties.

```python
async def find_by_source(self, source_name: str, properties: Dict[str, Any]) -> List[Thread]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_name` | str | Yes | Name of the source |
| `properties` | Dict[str, Any] | Yes | Source properties to match |

#### Returns

| Type | Description |
|------|-------------|
| List[Thread] | List of matching threads |

#### Example

```python
# Find threads from a specific source
threads = await store.find_by_source("slack", {
    "channel": "general",
    "team": "engineering"
})
```

### delete

Delete a thread by ID.

```python
async def delete(self, thread_id: str) -> bool
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | str | Yes | ID of the thread to delete |

#### Returns

| Type | Description |
|------|-------------|
| bool | True if thread was deleted, False if not found |

#### Example

```python
deleted = await store.delete("thread_123")
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TYLER_DB_ECHO` | Enable SQL query logging when "true" | false |
| `TYLER_DB_POOL_SIZE` | Database connection pool size (PostgreSQL only) | None |
| `TYLER_DB_MAX_OVERFLOW` | Maximum pool overflow (PostgreSQL only) | None |

## Best Practices

1. **Initialization**
   ```python
   # Always initialize before use
   store = ThreadStore()
   await store.initialize()
   ```

2. **Production Setup**
   ```python
   # Use PostgreSQL for production
   store = ThreadStore("postgresql+asyncpg://user:pass@localhost/dbname")
   
   # Configure pool size for better performance
   os.environ["TYLER_DB_POOL_SIZE"] = "20"
   os.environ["TYLER_DB_MAX_OVERFLOW"] = "10"
   ```

3. **Development Setup**
   ```python
   # Use SQLite for development
   store = ThreadStore("sqlite+aiosqlite:///dev.db")
   ```

4. **Attachment Handling**
   ```python
   # ThreadStore automatically handles attachment storage
   message = Message(content="With attachment", attachments=[attachment])
   thread.add_message(message)
   await store.save(thread)  # Attachments are stored automatically
   ```

## See Also

- [Thread API](./thread.md)
- [Message API](./message.md)
- [Attachment API](./attachment.md)
- [Database Storage Examples](../examples/database-storage.md) 