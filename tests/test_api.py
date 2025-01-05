import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
import json
import os

# Mock weave.init and litellm before importing api
with patch('weave.init') as mock_weave_init, \
     patch('litellm.completion') as mock_completion:
    mock_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Test response"))]
    )
    from api import app, slack_client, tyler_agent, thread_store, signature_verifier

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
    with patch('tools.slack.SlackClient') as mock:
        yield mock

@pytest.fixture
def mock_tyler_agent():
    """Mock Tyler agent"""
    with patch('models.TylerAgent.TylerAgent') as mock:
        yield mock

@pytest.fixture
def mock_thread_store():
    """Mock thread store"""
    with patch('database.thread_store.ThreadStore') as mock:
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
        assert response.data.decode() == "invalid request"

def test_slack_events_app_mention(client, mock_slack_signature):
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
    
    with patch('handlers.slack_handlers.SlackEventHandler.handle_mention') as mock_handle:
        response = client.post('/slack/events',
                             json=event_data,
                             headers={"X-Slack-Signature": "valid", "X-Slack-Request-Timestamp": "123"})
        
        assert response.status_code == 200
        mock_handle.assert_called_once_with(event_data["event"])

def test_trigger_tyler_success(client, mock_slack_signature):
    """Test successful Tyler trigger"""
    thread_id = "test-conv-123"
    
    with patch('models.TylerAgent.TylerAgent.go') as mock_go:
        response = client.post('/trigger/tyler',
                             json={"thread_id": thread_id},
                             headers={"X-Slack-Signature": "valid", "X-Slack-Request-Timestamp": "123"})
        
        assert response.status_code == 200
        assert response.data.decode() == "Processing started"
        mock_go.assert_called_once_with(thread_id)

def test_trigger_tyler_missing_thread_id(client, mock_slack_signature):
    """Test Tyler trigger without thread_id"""
    response = client.post('/trigger/tyler',
                          json={},
                          headers={"X-Slack-Signature": "valid", "X-Slack-Request-Timestamp": "123"})
    
    assert response.status_code == 400
    assert response.data.decode() == "thread_id is required"

def test_trigger_tyler_error(client, mock_slack_signature):
    """Test Tyler trigger with error"""
    thread_id = "test-conv-123"
    error_message = "Processing error"
    
    with patch('models.TylerAgent.TylerAgent.go') as mock_go:
        mock_go.side_effect = Exception(error_message)
        response = client.post('/trigger/tyler',
                             json={"thread_id": thread_id},
                             headers={"X-Slack-Signature": "valid", "X-Slack-Request-Timestamp": "123"})
        
        assert response.status_code == 500
        assert response.data.decode() == f"Error: {error_message}"

def test_slack_events_unknown_event(client, mock_slack_signature):
    """Test handling unknown event type"""
    event_data = {
        "type": "event_callback",
        "event": {
            "type": "unknown_event",
            "user": "U123"
        }
    }
    
    response = client.post('/slack/events',
                          json=event_data,
                          headers={"X-Slack-Signature": "valid", "X-Slack-Request-Timestamp": "123"})
    
    assert response.status_code == 200
    assert response.data.decode() == "" 