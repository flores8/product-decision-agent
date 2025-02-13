from dotenv import load_dotenv
from tyler.models.agent import Agent
from tyler.models.thread import Thread, Message
import weave
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

try:
    if os.getenv("WANDB_API_KEY"):
        weave.init("tyler")
        logger.info("Weave tracing initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize weave tracing: {e}. Continuing without weave.")

def post_to_slack_implementation(message: str, channel: str = "#general") -> str:
    """
    Implementation of the Slack posting tool.
    In a real application, this would use the Slack API to post messages.
    """
    # This is a mock implementation
    return f"Message posted to Slack channel {channel}: {message}"

# Define custom Slack posting tool that can be implemented either synchronously or asynchronously
custom_slack_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "post_to_slack",
            "description": "Post a message to a Slack channel",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to post to Slack"
                    },
                    "channel": {
                        "type": "string",
                        "description": "The Slack channel to post to (default: #general)",
                        "default": "#general"
                    }
                },
                "required": ["message"]
            }
        }
    },
    "implementation": post_to_slack_implementation
}

# Initialize the agent with both built-in and custom tools
agent = Agent(
    model_name="gpt-4",
    purpose="To help with web browsing and posting content to Slack",
    tools=[
        "web",          # Load the web tools module
        custom_slack_tool,     # Add our Slack posting tool
    ]
)

async def main():
    # Create a thread with a user question
    thread = Thread()

    # Add a user message
    message = Message(
        role="user",
        content="Please fetch the article at https://www.adamwdraper.com/learnings/2021/7/17/leadership, summarize its key points about leadership style, and post the summary to Slack."
    )
    thread.add_message(message)

    # Process the thread - the agent will use both web and Slack tools
    processed_thread, new_messages = await agent.go(thread)

    # Print all non-user messages (assistant responses and tool results)
    for message in new_messages:
        print(f"{message.role.capitalize()}: {message.content}")

if __name__ == "__main__":
    asyncio.run(main()) 