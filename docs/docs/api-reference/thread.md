---
sidebar_position: 2
---

# Thread API

The `Thread` class manages conversations and maintains context between messages. It's responsible for organizing messages, handling system prompts, and storing conversation metadata.

## Initialization

```python
from tyler.models.thread import Thread
from datetime import datetime, UTC

# Create a new thread
thread = Thread()

# Create a thread with custom parameters
thread = Thread(
    title="My Thread",
    messages=[],
    attributes={},
    source={"name": "slack", "thread_id": "123"}
)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `id` | str | No | UUID4 | Unique thread identifier |
| `title` | str | No | "Untitled Thread" | Thread title |
| `messages` | List[Message] | No | [] | List of messages |
| `created_at` | datetime | No | now(UTC) | Creation timestamp |
| `updated_at` | datetime | No | now(UTC) | Last update timestamp |
| `attributes` | Dict | No | {} | Custom metadata |
| `source` | Dict | No | None | Source information |

## Methods

### add_message

Add a new message to the thread and update analytics.

```python
def add_message(
    self,
    message: Message
) -> None
```

Messages are sequenced based on their role:
- System messages always get sequence 0 and are inserted at the beginning
- Other messages get incremental sequence numbers starting at 1

#### Example

```python
message = Message(role="user", content="Hello!")
thread.add_message(message)
```

### ensure_system_prompt

Ensures a system prompt exists as the first message in the thread.

```python
def ensure_system_prompt(
    self,
    prompt: str
) -> None
```

Only adds a system message if none exists at the start of the thread.

### get_messages_for_chat_completion

Return messages in the format expected by chat completion APIs.

```python
def get_messages_for_chat_completion(self):
    """
    Returns:
        List[Dict]: Messages formatted for chat completion
    """
```

### clear_messages

Clear all messages from the thread.

```python
def clear_messages(self) -> None
```

### get_last_message_by_role

Return the last message with the specified role.

```python
def get_last_message_by_role(self, role):
    """
    Get the last message with the specified role.
    
    Args:
        role: One of "user", "assistant", "system", "tool"
    
    Returns:
        Optional[Message]: The last message with the specified role, if any
    """
```

### generate_title

Generate a concise title for the thread using GPT-4o.

```python
@weave.op()
def generate_title(self) -> str
```

### get_total_tokens

Get total token usage across all messages in the thread.

```python
def get_total_tokens(self):
    """
    Returns:
        Dict: Token usage statistics
    """
```

Returns:
```python
{
    "overall": {
        "completion_tokens": int,
        "prompt_tokens": int,
        "total_tokens": int
    },
    "by_model": {
        "model_name": {
            "completion_tokens": int,
            "prompt_tokens": int,
            "total_tokens": int
        }
    }
}
```

### get_model_usage

Get usage statistics for a specific model or all models.

```python
def get_model_usage(self, model_name=None):
    """
    Args:
        model_name: Optional model name to filter by
    
    Returns:
        Dict: Per-model statistics including calls and token usage
    """
```

Returns per-model statistics including:
- Number of calls
- Token usage (completion, prompt, total)

### get_message_timing_stats

Calculate timing statistics across all messages.

```python
def get_message_timing_stats(self) -> Dict[str, Any]
```

Returns:
```python
{
    "total_latency": float,
    "average_latency": float,
    "message_count": int
}
```

### get_message_counts

Get count of messages by role.

```python
def get_message_counts(self) -> Dict[str, int]
```

Returns:
```python
{
    "system": int,
    "user": int,
    "assistant": int,
    "tool": int
}
```

### get_tool_usage

Get count of tool function calls in the thread.

```python
def get_tool_usage(self) -> Dict[str, Any]
```

Returns:
```python
{
    "tools": {
        "tool_name": call_count
    },
    "total_calls": int
}
```

### to_dict

Convert thread to a dictionary suitable for JSON serialization.

```python
def to_dict(self) -> Dict[str, Any]
```

## Field Validators

### ensure_timezone

Ensures all datetime fields are timezone-aware UTC.

```python
@field_validator("created_at", "updated_at", mode="before")
def ensure_timezone(cls, value):
    """
    Args:
        value: datetime value to validate
    
    Returns:
        datetime: Timezone-aware UTC datetime
    """
```

## Best Practices

1. **Message Management**
   ```python
   # Add messages in sequence
   thread.add_message(Message(role="user", content="Question"))
   thread.add_message(Message(role="assistant", content="Answer"))
   
   # Get last user message
   last_user_msg = thread.get_last_message_by_role("user")
   ```

2. **System Prompts**
   ```python
   # Ensure system prompt exists
   thread.ensure_system_prompt("You are a helpful assistant...")
   ```

3. **Analytics and Monitoring**
   ```python
   # Check token usage
   token_stats = thread.get_total_tokens()
   print(f"Total tokens: {token_stats['overall']['total_tokens']}")
   
   # Monitor tool usage
   tool_stats = thread.get_tool_usage()
   print(f"Total tool calls: {tool_stats['total_calls']}")
   ```

4. **Thread Organization**
   ```python
   # Generate meaningful title
   title = await thread.generate_title()
   
   # Track source
   thread = Thread(
       source={
           "name": "slack",
           "channel": "C123",
           "thread_ts": "1234567890.123"
       }
   )
   ```

## See Also

- [Agent API](./agent.md)
- [Message API](./message.md)
- [Examples](../examples/index.md) 