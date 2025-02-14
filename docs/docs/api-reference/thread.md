---
sidebar_position: 2
---

# Thread API

The `Thread` class manages conversations and maintains context between messages. It's responsible for organizing messages, handling system prompts, and storing conversation metadata.

## Initialization

```python
from tyler.models.thread import Thread

thread = Thread(
    id: str = None,
    system_prompt: str = None,
    attributes: Dict = None,
    messages: List[Message] = None,
    created_at: datetime = None,
    updated_at: datetime = None
)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | str | No | None | Unique thread identifier |
| `system_prompt` | str | No | None | System prompt for the thread |
| `attributes` | Dict | No | None | Custom metadata |
| `messages` | List[Message] | No | None | Initial messages |
| `created_at` | datetime | No | None | Creation timestamp |
| `updated_at` | datetime | None | None | Last update timestamp |

## Methods

### add_message

Add a message to the thread.

```python
def add_message(
    self,
    message: Message
) -> None
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | Message | Yes | Message to add |

#### Example

```python
message = Message(role="user", content="Hello!")
thread.add_message(message)
```

### get_messages

Get all messages in the thread.

```python
def get_messages(
    self,
    role: str = None,
    limit: int = None,
    offset: int = None
) -> List[Message]
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `role` | str | No | None | Filter by message role |
| `limit` | int | No | None | Maximum messages to return |
| `offset` | int | No | None | Number of messages to skip |

#### Returns

| Type | Description |
|------|-------------|
| List[Message] | List of messages |

#### Example

```python
# Get all messages
messages = thread.get_messages()

# Get last 5 assistant messages
assistant_msgs = thread.get_messages(role="assistant", limit=5)
```

### clear_messages

Remove all messages from the thread.

```python
def clear_messages(self) -> None
```

#### Example

```python
thread.clear_messages()
```

### update_system_prompt

Update the thread's system prompt.

```python
def update_system_prompt(
    self,
    prompt: str
) -> None
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | str | Yes | New system prompt |

#### Example

```python
thread.update_system_prompt("You are a helpful assistant...")
```

### set_attribute

Set a custom attribute.

```python
def set_attribute(
    self,
    key: str,
    value: Any
) -> None
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | str | Yes | Attribute key |
| `value` | Any | Yes | Attribute value |

#### Example

```python
thread.set_attribute("source", "slack")
```

### get_attribute

Get a custom attribute.

```python
def get_attribute(
    self,
    key: str,
    default: Any = None
) -> Any
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `key` | str | Yes | Attribute key |
| `default` | Any | No | Default value |

#### Returns

| Type | Description |
|------|-------------|
| Any | Attribute value or default |

#### Example

```python
source = thread.get_attribute("source", default="unknown")
```

## Properties

### id

Get the thread identifier.

```python
@property
def id(self) -> str:
    return self._id
```

### system_prompt

Get the current system prompt.

```python
@property
def system_prompt(self) -> str:
    return self._system_prompt
```

### messages

Get all messages in order.

```python
@property
def messages(self) -> List[Message]:
    return self._messages
```

### attributes

Get all custom attributes.

```python
@property
def attributes(self) -> Dict:
    return self._attributes
```

### created_at

Get creation timestamp.

```python
@property
def created_at(self) -> datetime:
    return self._created_at
```

### updated_at

Get last update timestamp.

```python
@property
def updated_at(self) -> datetime:
    return self._updated_at
```

## Persistence

Threads can be stored and retrieved using different storage backends:

### In-Memory Storage

```python
# Create thread
thread = Thread()

# Add to memory store
memory_store.add_thread(thread)

# Retrieve thread
thread = memory_store.get_thread(thread.id)
```

### Database Storage

```python
from tyler.database import Database

# PostgreSQL
db = Database(db_type="postgresql")
await db.store_thread(thread)
thread = await db.get_thread(thread_id)

# SQLite
db = Database(db_type="sqlite")
await db.store_thread(thread)
thread = await db.get_thread(thread_id)
```

## Events

The Thread class emits events that can be subscribed to:

```python
from tyler.events import EventEmitter

def on_message_added(event):
    print(f"New message: {event.message.content}")

thread.events.on("message_added", on_message_added)
```

Available events:
- `message_added`: Emitted when a message is added
- `messages_cleared`: Emitted when messages are cleared
- `system_prompt_updated`: Emitted when system prompt changes
- `attribute_changed`: Emitted when an attribute changes

## Best Practices

1. **Message Management**
   ```python
   # Add messages in sequence
   thread.add_message(Message(role="user", content="Question 1"))
   thread.add_message(Message(role="assistant", content="Answer 1"))
   
   # Clear old messages periodically
   if len(thread.messages) > 100:
       thread.clear_messages()
   ```

2. **System Prompts**
   ```python
   # Set task-specific prompts
   if task_type == "coding":
       thread.update_system_prompt("You are a coding assistant...")
   elif task_type == "writing":
       thread.update_system_prompt("You are a writing assistant...")
   ```

3. **Attributes**
   ```python
   # Use attributes for metadata
   thread.set_attribute("user_id", "123")
   thread.set_attribute("session_start", datetime.now())
   
   # Check attributes safely
   user_id = thread.get_attribute("user_id", default="anonymous")
   ```

4. **Persistence**
   ```python
   # Save thread state regularly
   async def save_thread_state():
       await db.store_thread(thread)
       
   # Implement auto-save on changes
   thread.events.on("message_added", save_thread_state)
   ```

## See Also

- [Agent API](./agent.md)
- [Message API](./message.md)
- [Database API](./database.md)
- [Examples](../examples/index.md) 