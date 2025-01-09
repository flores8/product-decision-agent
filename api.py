from flask import Flask, request, make_response, jsonify
from slack_sdk.signature import SignatureVerifier
import os
import streamlit as st
from tools.slack import SlackClient
import logging
from models.Agent import Agent
from models.RouterAgent import RouterAgent
from models.Registry import Registry
from database.thread_store import ThreadStore
from utils.helpers import get_tools
import weave
from config import WEAVE_PROJECT, API_HOST, API_PORT
import uuid

# Initialize Weave
weave.init(WEAVE_PROJECT)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load secrets from environment variables or .streamlit/secrets.toml
def get_secret(key):
    return os.environ.get(key) or st.secrets.get(key)

# Set environment variables from secrets
os.environ["SLACK_BOT_TOKEN"] = get_secret("SLACK_BOT_TOKEN")
os.environ["SLACK_SIGNING_SECRET"] = get_secret("SLACK_SIGNING_SECRET")

app = Flask(__name__)

# Initialize shared instances after environment variables are set
slack_client = SlackClient()
thread_store = ThreadStore()

# Initialize agent registry and register agents
agent_registry = Registry()

# Register Noah agent our Notion agent
ethan = Agent(
    purpose="Your name is Ethan. You are an enginneering manager at our company.  You are responsible for ensuring that the company's engineering policies are up to date and accurate.  You can also search for information in Notion.",
    notes="""
Some relevant information to help you:
- Our company policies are found in Notion
- Updates to company policies are frequently announced in Notion
- When searching for information in Notion, generalize your search query to find the most relevant information and compare several pages to ensure you have the most accurate information.

You can also edit or comment on engineering policies in Notion.""",
    tools=get_tools("notion")
)
agent_registry.register_agent("Ethan", ethan)

# Register Harper agent our HR agent
harper = Agent(
    purpose="""You are a head of HR, and you are responsible for:
- answering questions about the company's HR policies.
- ensuring that the company's HR policies are up to date and accurate.
- giving advice on how to handle HR related issues.""",
    notes="""
Some relevant information to help you:
- Our company policies are found in Notion
- Updates to company policies are frequently announced in Notion
- When searching for information in Notion, generalize your search query to find the most relevant information and compare several pages to ensure you have the most accurate information.

You can also edit or comment on HR policies in Notion.""",
    tools=get_tools("notion")
)
agent_registry.register_agent("Harper", harper)

# Initialize router agent with registry
router_agent = RouterAgent(registry=agent_registry)

# Initialize Slack signature verifier
slack_signature_verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])

@app.route("/slack/events", methods=["POST"])
def slack_events():
    """Handle incoming Slack events.
    
    Validates Slack signatures and processes events into the standard message format
    before forwarding to /process/message.
    """
    data = request.json
    event_type = data.get("type")
    event_id = data.get("event_id")
    event = data.get("event", {})
    
    logger.info(f"Received Slack event - ID: {event_id}, Type: {event_type}, Event: {event.get('type')}, Channel: {event.get('channel')}, Thread: {event.get('thread_ts', event.get('ts'))}, User: {event.get('user')}")
    
    # Verify Slack signature
    if not slack_signature_verifier.is_valid_request(request.get_data(), request.headers):
        logger.warning("Invalid Slack signature received")
        return make_response("Invalid request signature", 403)
        
    # Handle URL verification
    if event_type == "url_verification":
        logger.info("Handling Slack URL verification challenge")
        return jsonify({"challenge": data.get("challenge")})
        
    # Handle event callbacks
    if event_type == "event_callback":
        event = data.get("event", {})
        event_subtype = event.get("type")
        
        # Process both app_mention and message events
        if event_subtype in ["app_mention", "message"] and not event.get("bot_id") and not event.get("subtype"):
            channel = event.get('channel')
            thread_ts = event.get('thread_ts', event.get('ts'))
            user = event.get('user')
            text = event.get('text')

            logger.info(f"Processing Slack message - Channel: {channel}, Thread: {thread_ts}, User: {user}")

            if not all([channel, text, user]):
                logger.error("Missing required Slack event data", extra={
                    "channel": channel,
                    "text": bool(text),
                    "user": user
                })
                return make_response("", 200)

            # Format message for processing
            message_data = {
                "message": text,
                "source": {
                    "name": "slack",
                    "thread_id": thread_ts,
                    "channel": channel
                }
            }
            
            # Forward to process_message
            try:
                logger.info(f"Forwarding message to process_message - Thread: {thread_ts}")
                response = process_message(message_data)
                response_data = response.json
                
                # Send new assistant messages to Slack
                for msg in response_data["new_messages"]:
                    # Skip function messages and messages without content
                    if msg["role"] == "tool" or not msg.get("content"):
                        continue
                        
                    logger.info(f"Sending response to Slack - Thread: {thread_ts}")
                    slack_client.client.chat_postMessage(
                        channel=channel,
                        text=msg["content"],
                        thread_ts=thread_ts
                    )
                    
                return make_response("", 200)
            except Exception as e:
                logger.error(f"Error processing Slack message: {str(e)}", exc_info=True)
                return make_response(f"Error: {str(e)}", 500)
    
    return make_response("", 200)

@app.route("/process/message", methods=["POST"])
def process_message(message_data=None):
    """Process an incoming message from any source."""
    try:
        # Get message data from request if not provided
        if message_data is None:
            message_data = request.json
            
        logger.info("Processing message", extra={
            "source": message_data.get("source", {}).get("name"),
            "thread_id": message_data.get("source", {}).get("thread_id")
        })
            
        # Validate required fields
        if not isinstance(message_data, dict):
            logger.error("Invalid message_data format")
            return make_response("Invalid request format", 400)
            
        message = message_data.get("message")
        source = message_data.get("source")
        
        # Validate source object
        if not isinstance(source, dict) or not all(k in source for k in ["name", "thread_id"]):
            logger.error("Invalid source format in message_data")
            return make_response("Source must be an object with 'name' and 'thread_id' properties", 400)
            
        if not all([message, source["name"], source["thread_id"]]):
            logger.error("Missing required fields in message_data")
            return make_response("Missing required fields: message, source.name, and source.thread_id", 400)
            
        # Route the message and wait for processing to complete
        logger.info(f"Routing message to agent - Source: {source['name']}, Thread: {source['thread_id']}")
        processed_thread, new_messages = router_agent.route(
            message=message,
            source=source
        )
        
        logger.info(f"Message processing complete - Thread ID: {processed_thread.id}, New messages: {len(new_messages)}")
        
        # Return JSON response with both thread and new messages
        return jsonify({
            "thread": processed_thread.to_dict(),
            "new_messages": [msg.model_dump() for msg in new_messages]
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return make_response(f"Error: {str(e)}", 500)

if __name__ == "__main__":
    app.run(host=API_HOST, port=API_PORT, debug=True) 