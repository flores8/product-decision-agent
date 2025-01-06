from flask import Flask, request, make_response, jsonify
from slack_sdk.signature import SignatureVerifier
import os
import streamlit as st
from tools.slack import SlackClient
import logging
from models.Agent import Agent
from models.RouterAgent import RouterAgent
from models.Registry import Registry
from models.thread import Thread
from models.message import Message
from database.thread_store import ThreadStore
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
agent_registry.register_agent("tyler", Agent)

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
    # Verify Slack signature
    if not slack_signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid request signature", 403)
        
    data = request.json
    event_type = data.get("type")
    
    # Handle URL verification
    if event_type == "url_verification":
        return jsonify({"challenge": data.get("challenge")})
        
    # Handle event callbacks
    if event_type == "event_callback":
        event = data.get("event", {})
        
        # Only process non-bot messages
        if event.get("type") == "message" and not event.get("bot_id"):
            channel = event.get('channel')
            thread_ts = event.get('thread_ts', event.get('ts'))
            user = event.get('user')
            text = event.get('text')

            if not all([channel, text, user]):
                logger.error("Missing required Slack event data")
                return make_response("", 200)

            # Format message for processing
            message_data = {
                "message": text,
                "source": "slack",
                "metadata": {
                    "channel": channel,
                    "thread_ts": thread_ts,
                    "user": user,
                    "team_id": data.get("team_id"),
                    "api_app_id": data.get("api_app_id"),
                    "event_id": data.get("event_id"),
                    "event_time": data.get("event_time")
                }
            }
            
            # Forward to process_message
            try:
                response = process_message(message_data)
                return jsonify(response), 200
            except Exception as e:
                logger.error(f"Error processing Slack message: {str(e)}")
                return make_response(f"Error: {str(e)}", 500)
    
    return make_response("", 200)

@app.route("/process/message", methods=["POST"])
def process_message(message_data=None):
    """Process an incoming message from any source.
    
    Expected request format:
    {
        "message": str,  # The message content
        "source": str,  # Name of the source (e.g. "slack", "email")
        "metadata": dict  # Source-specific metadata
    }
    
    Returns:
        - 200 with {"thread_id": str} if message was routed successfully
        - 400 if request format is invalid
        - 500 if processing fails
    """
    try:
        # Get message data from request if not provided
        if message_data is None:
            message_data = request.json
            
        # Validate required fields
        if not isinstance(message_data, dict):
            return make_response("Invalid request format", 400)
            
        message = message_data.get("message")
        source = message_data.get("source")
        metadata = message_data.get("metadata", {})
        
        if not all([message, source]):
            return make_response("Missing required fields: message and source", 400)
            
        # Route the message
        thread_id = router_agent.route_message(
            message=message,
            source=source,
            metadata=metadata
        )
        return {"thread_id": thread_id}
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return make_response(f"Error: {str(e)}", 500)

@app.route("/sources", methods=["GET"])
def list_sources():
    """List all supported message sources.
    
    Returns:
        A JSON object containing:
        {
            "sources": list[str]  # List of supported source names
        }
    """
    return jsonify({
        "sources": ["slack", "email", "api"]  # Add other sources as they're supported
    })

if __name__ == "__main__":
    app.run(host=API_HOST, port=API_PORT, debug=True) 