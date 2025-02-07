from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message
from tyler.database.thread_store import ThreadStore
import weave
import asyncio

# Load environment variables from .env file
load_dotenv()

# Initialize weave (with a project name) for logging and tracing of all calls... trust me, you want this
weave.init("tyler")

def get_weather_implementation(location: str) -> str:
    """
    Implementation of the weather tool.
    In a real application, this would call a weather API.
    """
    # This is a mock implementation
    return f"The weather in {location} is sunny with a temperature of 72°F"

async def get_weather_async_implementation(location: str) -> str:
    """
    Async implementation of the weather tool.
    In a real application, this would call a weather API asynchronously.
    """
    # Simulate async API call
    await asyncio.sleep(1)
    return f"The weather in {location} is sunny with a temperature of 72°F (async)"

# Define custom weather tools with both sync and async implementations
weather_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and country"
                    }
                },
                "required": ["location"]
            }
        }
    },
    "implementation": get_weather_implementation
}

weather_async_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "get_weather_async",
            "description": "Get the current weather for a location (async version)",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and country"
                    }
                },
                "required": ["location"]
            }
        }
    },
    "implementation": get_weather_async_implementation
}

async def main():
    # Initialize thread store with the default SQLite database
    thread_store = ThreadStore()

    # Initialize agent with both built-in and custom tools
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help with weather information and web browsing",
        tools=[
            "web",          # Load the web tools module
            "command_line", # Load the command line tools module
            weather_tool,   # Add our sync weather tool
            weather_async_tool  # Add our async weather tool
        ],
        thread_store=thread_store  # Pass the thread store instance
    )

    # Create a thread with a user question
    thread = Thread()
    await thread_store.save(thread)  # Save the thread before using it

    message = Message(
        role="user",
        content="What's the weather like in San Francisco and New York? Please use both sync and async tools."
    )
    thread.add_message(message)
    await thread_store.save(thread)  # Save again after adding the message

    # Process the thread - the agent will use both sync and async tools
    processed_thread, new_messages = await agent.go(thread.id)

    # Print all non-user messages (assistant responses and tool results)
    for message in new_messages:
        print(f"{message.role.capitalize()}: {message.content}")

if __name__ == "__main__":
    asyncio.run(main()) 