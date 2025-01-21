from dotenv import load_dotenv
import os
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message

# Load environment variables from .env file
load_dotenv()

# Initialize the agent without thread store
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with data analysis and general questions",
    notes="Custom notes about the agent's behavior",
    temperature=0.7
)

# Create a new thread
thread = Thread()

# Add a user message
message = Message(
    role="user",
    content="What is the distance between Earth and Moon?"
)
thread.add_message(message)

# Process the thread by passing Thread object directly
processed_thread, new_messages = agent.go(thread)

# Print the assistant's response
for message in new_messages:
    if message.role == "assistant":
        print(f"Assistant: {message.content}") 