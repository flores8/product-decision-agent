import pytest
from unittest.mock import patch, MagicMock
from tools.slack import (
    SlackClient,
    post_to_slack,
    generate_slack_blocks,
    send_ephemeral_message,
    reply_in_thread
)

@pytest.fixture
def mock_env_token(monkeypatch):
    """Fixture to mock SLACK_BOT_TOKEN environment variable"""
    monkeypatch.setenv("SLACK_BOT_TOKEN", "mock-token")

@pytest.fixture
def mock_slack_client():
    """Fixture to create a mock Slack client"""
    with patch('slack_sdk.WebClient') as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.chat_postMessage.return_value = {"ok": True}
        mock_instance.chat_postEphemeral.return_value = {"ok": True}
        yield mock_instance

def test_slack_client_init_missing_token(monkeypatch):
    """Test SlackClient initialization with missing token"""
    # Clear both environment variable and streamlit secrets
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    with patch('streamlit.secrets', new={}):
        with pytest.raises(ValueError, match="SLACK_BOT_TOKEN environment variable is required"):
            SlackClient()

def test_slack_client_init(mock_env_token):
    """Test SlackClient initialization with token"""
    client = SlackClient()
    assert client.token == "mock-token"

@patch('tools.slack.SlackClient')
def test_post_to_slack(mock_slack_client):
    """Test posting messages to Slack"""
    mock_instance = MagicMock()
    mock_instance.client.chat_postMessage.return_value = {"ok": True}
    mock_slack_client.return_value = mock_instance

    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "Test message"}}]
    
    # Test with channel name without #
    result = post_to_slack(channel="general", blocks=blocks)
    assert result is True
    mock_instance.client.chat_postMessage.assert_called_with(
        channel="#general",
        blocks=blocks
    )

    # Test with channel name with #
    result = post_to_slack(channel="#general", blocks=blocks)
    assert result is True
    mock_instance.client.chat_postMessage.assert_called_with(
        channel="#general",
        blocks=blocks
    )

@patch('litellm.completion')
def test_generate_slack_blocks(mock_completion):
    """Test generating Slack blocks from content"""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='[{"type": "section", "text": {"type": "mrkdwn", "text": "Test content"}}]'
            )
        )
    ]
    mock_completion.return_value = mock_response

    result = generate_slack_blocks(content="Test content")
    assert isinstance(result, list)
    assert result[0]["type"] == "section"
    assert result[0]["text"]["text"] == "Test content"

    # Test error handling with invalid JSON response
    mock_response.choices[0].message.content = "Invalid JSON"
    result = generate_slack_blocks(content="Test content")
    assert isinstance(result, list)
    assert "Error" in result[0]["text"]["text"]

@patch('tools.slack.SlackClient')
def test_send_ephemeral_message(mock_slack_client):
    """Test sending ephemeral messages"""
    mock_instance = MagicMock()
    mock_instance.client.chat_postEphemeral.return_value = {"ok": True}
    mock_slack_client.return_value = mock_instance

    result = send_ephemeral_message(
        channel="general",
        user="U123",
        text="Test message"
    )
    
    assert result is True
    mock_instance.client.chat_postEphemeral.assert_called_with(
        channel="general",
        user="U123",
        text="Test message"
    )

@patch('tools.slack.SlackClient')
def test_reply_in_thread(mock_slack_client):
    """Test replying in threads"""
    mock_instance = MagicMock()
    mock_instance.client.chat_postMessage.return_value = {"ok": True}
    mock_slack_client.return_value = mock_instance

    result = reply_in_thread(
        channel="general",
        thread_ts="1234567890.123",
        text="Test reply",
        broadcast=True
    )
    
    assert result is True
    mock_instance.client.chat_postMessage.assert_called_with(
        channel="general",
        thread_ts="1234567890.123",
        text="Test reply",
        reply_broadcast=True
    )

def test_error_handling_in_functions(mock_env_token, mock_slack_client):
    """Test error handling in Slack functions"""
    # Set up error behavior for all Slack API calls
    mock_slack_client.chat_postMessage.side_effect = Exception("API Error")
    mock_slack_client.chat_postEphemeral.side_effect = Exception("API Error")
    
    # Test error handling in post_to_slack
    result = post_to_slack(channel="general", blocks=[])
    assert result is False

    # Test error handling in send_ephemeral_message
    result = send_ephemeral_message(channel="general", user="U123", text="test")
    assert result is False

    # Test error handling in reply_in_thread
    result = reply_in_thread(channel="general", thread_ts="123", text="test")
    assert result is False 