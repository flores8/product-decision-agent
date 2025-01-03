from flask import Flask, request, make_response
from slack_sdk.signature import SignatureVerifier
import os
import streamlit as st
from tools.slack import SlackClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load secrets from .streamlit/secrets.toml
os.environ["SLACK_BOT_TOKEN"] = st.secrets["SLACK_BOT_TOKEN"]
os.environ["SLACK_SIGNING_SECRET"] = st.secrets["SLACK_SIGNING_SECRET"]

app = Flask(__name__)
slack_client = SlackClient()
signature_verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])

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
        logger.info("Handling URL verification challenge")
        return make_response(
            challenge,
            200,
            {"content-type": "text/plain"}
        )
    
    # Handle mentions
    if event_data.get("type") == "event_callback":
        event = event_data.get("event", {})
        if event.get("type") == "app_mention":
            logger.info(f"Handling app mention from user: {event.get('user')}")
            slack_client.handle_mention(event)
    
    return make_response("", 200) 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True) 