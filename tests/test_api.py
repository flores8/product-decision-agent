import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
import json
import os
from models.RouterAgent import RouterAgent
from models.Thread import Thread
from models.Message import Message

# Mock weave.init and litellm before importing api
with patch('weave.init') as mock_weave_init, \
     patch('litellm.completion') as mock_completion:
    mock_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))]
    )
    from api import app, slack_client, router_agent, thread_store

@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_slack_signature():
    """Mock valid Slack signature verification"""
    with patch('slack_sdk.signature.SignatureVerifier.is_valid_request') as mock:
        mock.return_value = True
        yield mock

@pytest.fixture
def mock_slack_client():
    """Mock Slack client"""
    with patch('api.slack_client.client') as mock:
        yield mock

@pytest.fixture
def mock_thread_store():
    """Mock thread store"""
    with patch('database.thread_store.ThreadStore') as mock:
        yield mock

@pytest.fixture
def mock_router_agent():
    """Mock router agent"""
    with patch('api.router_agent') as mock:
        yield mock

def test_slack_events_url_verification(client, mock_slack_signature):
    """Test URL verification challenge"""
    challenge = "test_challenge"
    response = client.post('/slack/events',
                          json={"type": "url_verification", "challenge": challenge},
                          headers={"X-Slack-Signature": "valid", "X-Slack-Request-Timestamp": "123"})
    
    assert response.status_code == 200
    assert response.json == {"challenge": challenge}
    assert response.content_type == "application/json"

def test_slack_events_invalid_signature(client):
    """Test request with invalid Slack signature"""
    with patch('slack_sdk.signature.SignatureVerifier.is_valid_request') as mock:
        mock.return_value = False
        response = client.post('/slack/events',
                             json={"type": "event_callback"},
                             headers={"X-Slack-Signature": "invalid", "X-Slack-Request-Timestamp": "123"})
        
        assert response.status_code == 403
        assert response.data.decode() == "Invalid request signature"

def test_slack_events_app_mention(client, mock_slack_signature, mock_router_agent, mock_slack_client):
    """Test handling app mention events"""
    event_data = {
        "type": "event_callback",
        "event": {
            "type": "app_mention",
            "user": "U123",
            "text": "Hello <@bot>",
            "ts": "123.456",
            "channel": "C123"
        }
    }
    
    # Mock router_agent.route to return a thread and messages
    mock_thread = MagicMock(spec=Thread)
    mock_thread.id = "test-thread-id"
    mock_thread.to_dict.return_value = {"id": "test-thread-id"}
    mock_message = MagicMock(spec=Message)
    mock_message.model_dump.return_value = {
        "role": "assistant",
        "content": "Test response"
    }
    mock_router_agent.route.return_value = (mock_thread, [mock_message])
    
    # Mock Slack client's chat_postMessage method
    mock_slack_client.chat_postMessage.return_value = {"ok": True, "ts": "123.456"}
    
    response = client.post('/slack/events',
                          json=event_data,
                          headers={"X-Slack-Signature": "valid", "X-Slack-Request-Timestamp": "123"})
    
    assert response.status_code == 200
    mock_router_agent.route.assert_called_once()
    mock_slack_client.chat_postMessage.assert_called_once_with(
        channel="C123",
        text="Test response",
        thread_ts="123.456"
    )

def test_process_message(client, mock_router_agent):
    """Test processing a message"""
    # Create mock thread and message
    mock_thread = MagicMock(spec=Thread)
    mock_thread.id = "test-thread-id"
    mock_thread.to_dict.return_value = {"id": "test-thread-id"}
    mock_message = MagicMock(spec=Message)
    mock_message.model_dump.return_value = {
        "role": "assistant",
        "content": "Test response"
    }
    
    # Mock router_agent.route
    mock_router_agent.route.return_value = (mock_thread, [mock_message])
    
    response = client.post("/process/message", json={
        "message": "test message",
        "source": {
            "name": "test_source",
            "thread_id": "test-thread-id"
        }
    })
    
    assert response.status_code == 200
    assert "thread" in response.json
    assert "new_messages" in response.json
    assert response.json["thread"]["id"] == "test-thread-id"
    assert len(response.json["new_messages"]) == 1

def test_process_message_invalid_request(client):
    """Test processing a message with invalid request format"""
    response = client.post("/process/message", json={
        "invalid": "format"
    })
    
    assert response.status_code == 400
    assert "Source must be an object with 'name' and 'thread_id' properties" in response.data.decode()

def test_process_message_missing_fields(client):
    """Test processing a message with missing required fields"""
    response = client.post("/process/message", json={
        "message": "test",
        "source": {
            "name": "test"
            # missing thread_id
        }
    })
    
    assert response.status_code == 400
    assert "Source must be an object with 'name' and 'thread_id' properties" in response.data.decode()

def test_process_message_error(client, mock_router_agent):
    """Test processing a message where an error occurs"""
    mock_router_agent.route.side_effect = Exception("Processing error")
    
    response = client.post("/process/message", json={
        "message": "test message",
        "source": {
            "name": "test_source",
            "thread_id": "test-thread-id"
        }
    })
    
    assert response.status_code == 500
    assert "Error: Processing error" in response.data.decode() 