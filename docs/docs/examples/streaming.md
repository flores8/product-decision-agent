# Streaming Responses

Tyler supports streaming responses from the agent, allowing you to build highly interactive applications that show responses in real-time. This example demonstrates how to use streaming with both basic responses and tool execution.

## Basic Streaming Example

Here's a simple example that shows how to stream responses from the agent:

```python
from tyler.models.agent import Agent, StreamUpdate
from tyler.models.thread import Thread
from tyler.models.message import Message
import asyncio

# Initialize the agent
agent = Agent(
    model_name="gpt-4o",
    purpose="To be a helpful assistant."
)

async def main():
    # Create a thread and add a user message
    thread = Thread()
    message = Message(
        role="user",
        content="Tell me about the benefits of exercise."
    )
    thread.add_message(message)

    print("Assistant: ", end="", flush=True)

    # Process the thread using go_stream
    async for update in agent.go_stream(thread):
        if update.type == StreamUpdate.Type.CONTENT_CHUNK:
            # Print content chunks as they arrive
            print(update.data, end="", flush=True)
        elif update.type == StreamUpdate.Type.ERROR:
            # Print any errors that occur
            print(f"\nError: {update.data}")
        elif update.type == StreamUpdate.Type.COMPLETE:
            # Final update contains (thread, new_messages)
            print()  # Add newline after completion

if __name__ == "__main__":
    asyncio.run(main())
```

## Streaming with Tools

This example shows how to use streaming with tool execution, demonstrating how to handle both content chunks and tool results:

```python
from tyler.models.agent import Agent, StreamUpdate
from tyler.models.thread import Thread
from tyler.models.message import Message
import asyncio

# Define a custom translator tool
def custom_translator_implementation(text: str, target_language: str) -> str:
    translations = {
        "spanish": {
            "hello": "hola",
            "world": "mundo"
        }
    }
    
    target_language = target_language.lower()
    text = text.lower()
    
    if target_language not in translations:
        return f"Error: Unsupported target language '{target_language}'"
        
    if text in translations[target_language]:
        return translations[target_language][text]
    else:
        return f"Mock translation to {target_language}: [{text}]"

# Define custom translator tool
custom_translator_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "translate",
            "description": "Translate text to another language",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to translate"
                    },
                    "target_language": {
                        "type": "string",
                        "description": "The target language for translation",
                        "enum": ["Spanish"]
                    }
                },
                "required": ["text", "target_language"]
            }
        }
    },
    "implementation": custom_translator_implementation
}

# Initialize the agent
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with translations.",
    tools=[custom_translator_tool]
)

async def main():
    # Create a thread and add a user message
    thread = Thread()
    message = Message(
        role="user",
        content="How do you say 'hello world' in Spanish?"
    )
    thread.add_message(message)

    print("Assistant: ", end="", flush=True)

    # Process the thread using go_stream
    async for update in agent.go_stream(thread):
        if update.type == StreamUpdate.Type.CONTENT_CHUNK:
            # Print content chunks as they arrive
            print(update.data, end="", flush=True)
        elif update.type == StreamUpdate.Type.TOOL_MESSAGE:
            # Print translation results on new lines
            tool_message = update.data
            print(f"\nTranslation: {tool_message.content}")
        elif update.type == StreamUpdate.Type.ERROR:
            # Print any errors that occur
            print(f"\nError: {update.data}")
        elif update.type == StreamUpdate.Type.COMPLETE:
            # Final update contains (thread, new_messages)
            print()  # Add newline after completion

if __name__ == "__main__":
    asyncio.run(main())
```

## Multiple Turns with Streaming

Here's an example that shows how to handle multiple conversation turns with streaming:

```python
from tyler.models.agent import Agent, StreamUpdate
from tyler.models.thread import Thread
from tyler.models.message import Message
import asyncio

# Initialize the agent
agent = Agent(
    model_name="gpt-4o",
    purpose="To be a helpful assistant."
)

async def main():
    # Example conversation with multiple turns
    conversations = [
        "Tell me about the benefits of exercise.",
        "What specific exercises are good for beginners?",
        "How often should beginners exercise?"
    ]

    # Create a single thread for the entire conversation
    thread = Thread()

    for user_input in conversations:
        print(f"\nUser: {user_input}")
        
        # Add user message to thread
        message = Message(
            role="user",
            content=user_input
        )
        thread.add_message(message)

        print("\nAssistant: ", end="", flush=True)

        # Process the thread using go_stream
        async for update in agent.go_stream(thread):
            if update.type == StreamUpdate.Type.CONTENT_CHUNK:
                # Print content chunks as they arrive
                print(update.data, end="", flush=True)
            elif update.type == StreamUpdate.Type.TOOL_MESSAGE:
                # Print tool results on new lines
                tool_message = update.data
                print(f"\nTool: {tool_message.content}")
            elif update.type == StreamUpdate.Type.ERROR:
                # Print any errors that occur
                print(f"\nError: {update.data}")
            elif update.type == StreamUpdate.Type.COMPLETE:
                # Final update contains (thread, new_messages)
                print()  # Add newline after completion
        
        print("\n" + "-"*50)  # Separator between conversations

if __name__ == "__main__":
    asyncio.run(main())
```

## Best Practices for Streaming

1. **Flush Output**: When printing streamed content, always use `flush=True` to ensure immediate display.
2. **Error Handling**: Always handle `StreamUpdate.Type.ERROR` to catch and display any issues.
3. **Tool Results**: Display tool results on new lines to avoid mixing with streamed content.
4. **Completion Handling**: Use `StreamUpdate.Type.COMPLETE` to perform any cleanup or final processing.
5. **Buffer Management**: For web applications, implement proper buffer management to handle long streams. 