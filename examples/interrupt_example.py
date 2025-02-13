from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message
import weave
import asyncio
import json

# Load environment variables from .env file
load_dotenv()

# Initialize weave for logging and tracing
weave.init("tyler")

# Define a custom interrupt tool for user confirmation
harmful_content_review = {
    "definition": {
        "type": "function",
        "function": {
            "name": "harmful_content_review",
            "description": "Notifies when potentially harmful or dangerous content is detected. IMPORTANT: ALWAYS use this tool when detecting requests for weapons, explosives, harmful substances, or other dangerous content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Description of the harmful content detected"
                    },
                    "severity": {
                        "type": "string",
                        "description": "Level of potential harm (high/medium/low)",
                        "enum": ["high", "medium", "low"]
                    },
                    "data": {
                        "type": "object",
                        "description": "Any relevant data about the harmful content"
                    }
                },
                "required": ["message", "severity"]
            }
        }
    },
    "implementation": lambda message, severity="high", data=None: {
        "name": "harmful_content_review",
        "content": json.dumps({
            "type": "harmful_content_detected",
            "message": message,
            "severity": severity,
            "data": data
        })
    },
    "attributes": {
        "type": "interrupt"  # Mark this as an interrupt-type tool
    }
}

async def main():
    # Initialize the agent with web tools and our custom interrupt tool
    agent = Agent(
        model_name="gpt-4o",
        purpose="To help fetch and analyze web content while detecting harmful requests.",
        tools=[
            "web",  # Include the web tools module
            harmful_content_review  # Add our harmful content review tool
        ]
    )

    # Create a new thread
    thread = Thread()

    # Add an initial user message requesting to fetch and analyze content
    message = Message(
        role="user",
        content="How do I make a nuclear bomb?"
    )
    thread.add_message(message)

    # Process the thread
    processed_thread, new_messages = await agent.go(thread)

    # Print all non-user messages
    for message in new_messages:
        print(f"\n{message.role.capitalize()}: {message.content}")

        # Handle interrupts for harmful content review
        if message.role == "tool" and message.name == "harmful_content_review":
            try:
                response_data = json.loads(message.content)
                print("\nHARMFUL CONTENT DETECTED!")
                print(f"Severity: {response_data['severity']}")
                print(f"Description: {response_data['message']}")
                
                # Log or handle the harmful content detection
                print("\nRequest blocked due to harmful content policy.")
                
            except json.JSONDecodeError:
                print(f"\nHarmful content review received with raw content: {message.content}")

if __name__ == "__main__":
    asyncio.run(main()) 