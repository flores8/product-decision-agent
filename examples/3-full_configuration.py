from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.database.thread_store import ThreadStore
import asyncio
import weave
import os

# Load environment variables from .env file
load_dotenv()

# Initialize weave for tracing (optional - requires WANDB_API_KEY environment variable)
if os.getenv("WANDB_API_KEY"):
    weave.init("tyler")

# Example custom tool implementation
async def get_weather_async(location: str) -> str:
    """
    Async implementation of the weather tool.
    In a real application, this would call a weather API asynchronously.
    """
    # Simulate async API call
    await asyncio.sleep(0.5)
    return f"The weather in {location} is sunny with a temperature of 72°F"

# Define custom weather tool
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
    "implementation": get_weather_async
}

# Initialize thread store with SQLite database
thread_store = ThreadStore()

# Initialize agent with all available configuration options
agent = Agent(
    # Core LLM settings
    model_name="gpt-4o",          # The LLM model to use
    temperature=0.7,              # Controls randomness in responses (0.0 to 1.0)
    
    # Agent identity and behavior
    name="WeatherBot",            # Custom name for the agent
    purpose="To demonstrate agent configuration with weather information capabilities",
    notes="""
    Key capabilities and guidelines:
    - Provides weather information using custom weather tool
    - Uses web tools for additional real-time information when needed
    - Executes command line operations when required
    - Maintains conversation history in SQLite database
    - Gives clear, concise responses with context
    """,
    
    # Tools configuration
    tools=[
        "web",                    # Built-in web tools module
        "command_line",           # Built-in command line tools
        weather_tool,             # Custom weather information tool
    ],
    max_tool_recursion=10,        # Maximum number of recursive tool calls
    
    # Storage configuration
    thread_store=thread_store     # Use SQLite for persistent storage
)

async def main():
    # Create a new thread
    thread = Thread()
    await thread_store.save(thread)

    # Add a user message that will demonstrate multiple capabilities
    message = Message(
        role="user",
        content="""Please help me with the following:
1. What's the current weather in Tokyo?
2. Compare that with the weather in New York
3. List the contents of the current directory"""
    )
    thread.add_message(message)
    await thread_store.save(thread)

    # Process the thread
    processed_thread, new_messages = await agent.go(thread.id)

    # Print all non-user messages
    for message in new_messages:
        if message.role == "assistant":
            print(f"\n{agent.name}: {message.content}")
        elif message.role == "tool":
            print(f"\nTool ({message.name}): {message.content}")

if __name__ == "__main__":
    asyncio.run(main()) 