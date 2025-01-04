from flask import Flask, request, make_response, jsonify
from slack_sdk.signature import SignatureVerifier
import os
import streamlit as st
from tools.slack import SlackClient
import logging
from models.TylerAgent import TylerAgent
from models.conversation import Conversation
from database.conversation_store import ConversationStore
from handlers.slack_handlers import SlackEventHandler
import weave
from config import WEAVE_PROJECT, API_HOST, API_PORT

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
tyler_agent = TylerAgent()
conversation_store = ConversationStore()
signature_verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])
slack_handler = SlackEventHandler(slack_client, tyler_agent, conversation_store)

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

@app.route("/trigger/tyler", methods=["POST"])
def trigger_tyler():
    logger.info(f"Received Tyler trigger request: {request.json}")
    
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        logger.warning("Invalid request signature")
        return make_response("invalid request", 403)

    data = request.json
    conversation_id = data.get("conversation_id")
    
    if not conversation_id:
        return make_response("conversation_id is required", 400)
        
    try:
        tyler_agent.go(conversation_id)
        return make_response("Processing started", 200)
    except Exception as e:
        logger.error(f"Error processing Tyler request: {str(e)}")
        return make_response(f"Error: {str(e)}", 500)

if __name__ == "__main__":
    app.run(host=API_HOST, port=API_PORT, debug=True) 