---
sidebar_position: 1
---

# Agent API

The `Agent` class is the core component of Tyler, responsible for managing conversations and executing tasks.

## Initialization

```python
from tyler.models.agent import Agent

agent = Agent(
    model_name: str,
    purpose: str,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    tools: List[Dict] = None,
    system_prompt: str = None,
    attributes: Dict = None
)
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model_name` | str | Yes | - | The LLM model to use (e.g., "gpt-4o") |
| `purpose` | str | Yes | - | The agent's purpose or role |
| `temperature` | float | No | 0.7 | Response creativity (0.0-1.0) |
| `max_tokens` | int | No | 1000 | Maximum response length |
| `tools` | List[Dict] | No | None | List of custom tools |
| `system_prompt` | str | No | None | Custom system prompt |
| `attributes` | Dict | No | None | Custom metadata |

## Methods

### go

Process a thread and generate responses.

```python
async def go(
    self,
    thread: Thread,
    **kwargs
) -> Tuple[Thread, List[Message]]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread` | Thread | Yes | The thread to process |
| `**kwargs` | Dict | No | Additional parameters |

#### Returns

| Type | Description |
|------|-------------|
| Tuple[Thread, List[Message]] | Processed thread and new messages |

#### Example

```python
thread = Thread()
message = Message(role="user", content="Hello!")
thread.add_message(message)

processed_thread, new_messages = await agent.go(thread)
```

### execute_tool

Execute a specific tool.

```python
async def execute_tool(
    self,
    tool_name: str,
    parameters: Dict,
    **kwargs
) -> Any
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tool_name` | str | Yes | Name of the tool to execute |
| `parameters` | Dict | Yes | Tool parameters |
| `**kwargs` | Dict | No | Additional parameters |

#### Returns

| Type | Description |
|------|-------------|
| Any | Tool execution result |

#### Example

```python
result = await agent.execute_tool(
    tool_name="get_weather",
    parameters={"location": "London"}
)
```

### add_tool

Add a new tool to the agent.

```python
def add_tool(
    self,
    tool: Dict
) -> None
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tool` | Dict | Yes | Tool configuration |

#### Example

```python
weather_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string"
                    }
                }
            }
        }
    },
    "implementation": get_weather_function
}

agent.add_tool(weather_tool)
```

### remove_tool

Remove a tool from the agent.

```python
def remove_tool(
    self,
    tool_name: str
) -> None
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tool_name` | str | Yes | Name of tool to remove |

#### Example

```python
agent.remove_tool("get_weather")
```

### update_system_prompt

Update the agent's system prompt.

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
agent.update_system_prompt("You are a helpful assistant...")
```

## Properties

### tools

Get the list of available tools.

```python
@property
def tools(self) -> List[Dict]:
    return self._tools
```

### system_prompt

Get the current system prompt.

```python
@property
def system_prompt(self) -> str:
    return self._system_prompt
```

## Error Handling

The Agent class can raise several types of exceptions:

```python
try:
    result = await agent.go(thread)
except ModelError as e:
    # Handle model-related errors
    print(f"Model error: {e}")
except ToolExecutionError as e:
    # Handle tool execution errors
    print(f"Tool error: {e}")
except AgentError as e:
    # Handle general agent errors
    print(f"Agent error: {e}")
```

## Events

The Agent class emits events that can be subscribed to:

```python
from tyler.events import EventEmitter

def on_tool_execution(event):
    print(f"Tool executed: {event.tool_name}")

agent.events.on("tool_execution", on_tool_execution)
```

Available events:
- `tool_execution`: Emitted when a tool is executed
- `message_processed`: Emitted when a message is processed
- `error`: Emitted when an error occurs

## Best Practices

1. **Model Selection**
   ```python
   # For complex tasks
   agent = Agent(model_name="gpt-4o", temperature=0.7)
   
   # For simple tasks
   agent = Agent(model_name="gpt-3.5-turbo", temperature=0.5)
   ```

2. **Tool Management**
   ```python
   # Add tools selectively
   if needs_weather:
       agent.add_tool(weather_tool)
   
   # Remove tools when not needed
   if not needs_weather:
       agent.remove_tool("get_weather")
   ```

3. **Error Handling**
   ```python
   try:
       result = await agent.go(thread)
   except Exception as e:
       logger.error(f"Agent error: {e}")
       # Implement retry logic or fallback
   ```

4. **Performance Optimization**
   ```python
   # Use appropriate max_tokens
   agent = Agent(
       model_name="gpt-4o",
       max_tokens=500  # Adjust based on needs
   )
   
   # Implement caching
   from tyler.cache import Cache
   cache = Cache()
   agent.use_cache(cache)
   ```

## See Also

- [Thread API](./thread.md)
- [Message API](./message.md)
- [Tool API](./tool.md)
- [Examples](../examples/index.md) 