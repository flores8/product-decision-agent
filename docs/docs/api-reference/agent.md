---
sidebar_position: 1
---

# Agent API

The `Agent` class is the core component of Tyler, responsible for managing conversations and executing tasks. It uses Pydantic for data validation and Weave for monitoring and tracing.

## Initialization

```python
from tyler.models.agent import Agent

agent = Agent(
    model_name: str = "gpt-4o",
    temperature: float = 0.7,
    name: str = "Tyler",
    purpose: str = "To be a helpful assistant.",
    notes: str = "",
    tools: List[Union[str, Dict]] = [],
    max_tool_iterations: int = 10,
    thread_store: Optional[object] = MemoryThreadStore
)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model_name` | str | No | "gpt-4o" | The LLM model to use |
| `temperature` | float | No | 0.7 | Response creativity (0.0-1.0) |
| `name` | str | No | "Tyler" | Name of the agent |
| `purpose` | str | No | "To be a helpful assistant." | The agent's purpose or role |
| `notes` | str | No | "" | Additional notes for the agent |
| `tools` | List[Union[str, Dict]] | No | [] | List of tools (strings for built-in modules or dicts for custom tools) |
| `max_tool_iterations` | int | No | 10 | Maximum number of tool iterations |
| `thread_store` | Optional[object] | No | MemoryThreadStore | Thread storage implementation |

## Methods

### go

Process a thread and generate responses.

```python
async def go(
    self,
    thread_or_id: Union[str, Thread],
    new_messages: Optional[List[Message]] = None
) -> Tuple[Thread, List[Message]]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_or_id` | Union[str, Thread] | Yes | Thread object or thread ID to process |
| `new_messages` | Optional[List[Message]] | No | Messages added during this processing round |

#### Returns

| Type | Description |
|------|-------------|
| Tuple[Thread, List[Message]] | The processed thread and list of new non-user messages |

#### Example

```python
thread = Thread()
message = Message(role="user", content="Hello!")
thread.add_message(message)

processed_thread, new_messages = await agent.go(thread)
```

### go_stream

Process a thread with streaming updates. This method provides real-time updates as the agent processes the request.

```python
async def go_stream(
    self,
    thread: Thread
) -> AsyncGenerator[StreamUpdate, None]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread` | Thread | Yes | Thread object to process |

#### Returns

An async generator that yields `StreamUpdate` objects containing:
- Content chunks as they arrive
- Complete assistant messages with tool calls
- Tool execution results
- Final thread state
- Any errors that occur

#### StreamUpdate Types

| Type | Description | Data Content |
|------|-------------|--------------|
| `CONTENT_CHUNK` | Partial content from assistant | str |
| `ASSISTANT_MESSAGE` | Complete assistant message | Message |
| `TOOL_MESSAGE` | Tool execution result | Message |
| `COMPLETE` | Final thread state | Tuple[Thread, List[Message]] |
| `ERROR` | Error during processing | str |

#### Example

```python
thread = Thread()
message = Message(role="user", content="Hello!")
thread.add_message(message)

print("Assistant: ", end="", flush=True)
async for update in agent.go_stream(thread):
    if update.type == StreamUpdate.Type.CONTENT_CHUNK:
        # Print content chunks as they arrive
        print(update.data, end="", flush=True)
    elif update.type == StreamUpdate.Type.TOOL_MESSAGE:
        # Print tool results on new lines
        tool_message = update.data
        print(f"\nTool ({tool_message.name}): {tool_message.content}")
    elif update.type == StreamUpdate.Type.ERROR:
        # Print any errors that occur
        print(f"\nError: {update.data}")
    elif update.type == StreamUpdate.Type.COMPLETE:
        # Final update contains (thread, new_messages)
        print()  # Add newline after completion
```

### step

Execute a single step of the agent's processing.

```python
@weave.op()
async def step(
    self,
    thread: Thread,
    stream: bool = False
) -> Tuple[Any, Dict]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread` | Thread | Yes | The thread to process |
| `stream` | bool | No | Whether to stream the response |

#### Returns

| Type | Description |
|------|-------------|
| Tuple[Any, Dict] | The completion response and metrics |

## Private Methods

### _process_message_files

Process any files attached to a message.

```python
async def _process_message_files(
    self,
    message: Message
) -> None
```

### _get_completion

Get a completion from the LLM with weave tracing.

```python
@weave.op()
async def _get_completion(
    self,
    **completion_params
) -> Any
```

### _get_thread

Get thread object from ID or return the thread object directly.

```python
async def _get_thread(
    self,
    thread_or_id: Union[str, Thread]
) -> Thread
```

### _serialize_tool_calls

Serialize tool calls into a format suitable for storage.

```python
def _serialize_tool_calls(
    self,
    tool_calls
) -> Optional[List[Dict]]
```

### _process_tool_call

Process a single tool call and return whether to break the iteration.

```python
async def _process_tool_call(
    self,
    tool_call,
    thread: Thread,
    new_messages: List[Message]
) -> bool
```

### _handle_max_iterations

Handle the case when max iterations is reached.

```python
async def _handle_max_iterations(
    self,
    thread: Thread,
    new_messages: List[Message]
) -> Tuple[Thread, List[Message]]
```

### _handle_tool_execution

Execute a single tool call and format the result message.

```python
@weave.op()
async def _handle_tool_execution(
    self,
    tool_call
) -> dict
```

## Private Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `_prompt` | AgentPrompt | Handles system prompt generation |
| `_iteration_count` | int | Tracks tool iteration count |
| `_file_processor` | FileProcessor | Handles file processing |
| `_processed_tools` | List[Dict] | Stores processed tool definitions |

## Error Handling

```python
try:
    processed_thread, new_messages = await agent.go(thread)
except ValueError as e:
    # Handle validation errors (e.g., thread not found)
    print(f"Validation error: {e}")
except Exception as e:
    # Handle other errors
    print(f"Error: {e}")
```

## Tool Configuration

### Built-in Tool Modules

```python
agent = Agent(
    tools=[
        "web",      # Use built-in web tools
        "slack",    # Use built-in Slack tools
        "notion",   # Use built-in Notion tools
        "image",    # Use built-in image tools
        "command_line"  # Use built-in command line tools
    ]
)
```

### Custom Tools

```python
custom_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "custom_tool",
            "description": "Tool description",
            "parameters": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                }
            }
        }
    },
    "implementation": lambda param1: f"Result: {param1}",
    "attributes": {
        "type": "standard"  # or "interrupt"
    }
}

agent = Agent(tools=[custom_tool])
```

## Best Practices

1. **Thread Store Selection**
   ```python
   # For development/testing
   agent = Agent()  # Uses in-memory store
   
   # For production
   from tyler.database.thread_store import ThreadStore
   store = ThreadStore("postgresql://...")
   agent = Agent(thread_store=store)
   ```

2. **Tool Iteration Management**
   ```python
   # For complex workflows
   agent = Agent(max_tool_iterations=20)
   
   # For simple tasks
   agent = Agent(max_tool_iterations=5)
   ```

3. **File Processing**
   ```python
   # Message with file attachment
   message = Message(
       content="Process this file",
       file_content=file_bytes,
       filename="document.pdf"
   )
   thread.add_message(message)
   # Agent will automatically process files
   ```

4. **Monitoring with Weave**
   ```python
   # Enable Weave tracing
   import weave
   weave.init("tyler")
   
   # Traces will be available for step() and go() methods
   ```

## See Also

- [Thread API](./thread.md)
- [Message API](./message.md)
- [Examples](../examples/index.md) 