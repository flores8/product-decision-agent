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
from handlers.slack_handlers import SlackEventHandler
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
signature_verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])

# Initialize agent registry and register agents
agent_registry = Registry()
agent_registry.register_agent("tyler", Agent)

# Initialize router agent with registry
router_agent = RouterAgent(registry=agent_registry)

# Initialize slack handler with router agent instead of tyler agent
slack_handler = SlackEventHandler(slack_client, router_agent, thread_store)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    logger.info(f"Received Slack event: {request.json}")
    
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        logger.warning("Invalid request signature")
        return make_response("invalid request", 403)

    event_data = request.json
    
    # Handle URL verification
    if event_data.get("type") == "url_verification":
        challenge = event_data.get("challenge")
        logger.info(f"Received challenge: {challenge}")
        response = jsonify({"challenge": challenge})
        logger.info(f"Sending response: {response.get_data(as_text=True)}")
        return response
    
    # Handle mentions
    if event_data.get("type") == "event_callback":
        event = event_data.get("event", {})
        if event.get("type") == "app_mention":
            logger.info(f"Handling app mention from user: {event.get('user')}")
            slack_handler.handle_mention(event)
    
    return make_response("", 200) 

@app.route("/router", methods=["POST"])
def router():
    logger.info(f"Received router request: {request.json}")
    
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        logger.warning("Invalid request signature")
        return make_response("invalid request", 403)

    data = request.json
    message = data.get("message")
    thread_id = data.get("thread_id")
    
    if not message:
        return make_response("message is required", 400)
        
    try:
        # If thread_id provided, verify it exists
        if thread_id:
            thread = thread_store.get(thread_id)
            if not thread:
                return make_response(f"Thread '{thread_id}' not found", 404)
            
            # Add message to existing thread
            user_message = Message(role="user", content=message)
            thread.add_message(user_message)
            thread_store.save(thread)
            
            # Route the message
            router_agent.route(thread_id)
            return make_response("Processing started", 200)
        
        # For new messages without thread_id, let RouterAgent handle thread creation
        thread_id = router_agent.route_new_message(message)
        if not thread_id:
            return make_response("No agent assignment needed", 200)
            
        return make_response({"thread_id": thread_id, "status": "Processing started"}, 200)
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return make_response(f"Error: {str(e)}", 500)

@app.route("/agents", methods=["GET"])
def list_agents():
    """List all available agents"""
    return jsonify({
        "agents": agent_registry.list_agents()
    })

if __name__ == "__main__":
    app.run(host=API_HOST, port=API_PORT, debug=True) 