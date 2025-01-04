import pytest
import os
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def mock_streamlit_secrets():
    """Mock streamlit secrets for testing"""
    with patch('streamlit.secrets', new={
        'SLACK_BOT_TOKEN': 'test-bot-token',
        'SLACK_SIGNING_SECRET': 'test-signing-secret',
        'OPENAI_API_KEY': 'test-openai-key',
        'NOTION_TOKEN': 'test-notion-token',
        'WANDB_API_KEY': 'test-wandb-key'
    }):
        yield

@pytest.fixture(autouse=True)
def mock_openai():
    """Mock OpenAI/litellm calls for testing"""
    with patch('litellm.completion') as mock:
        mock.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))]
        )
        yield mock

@pytest.fixture(autouse=True)
def mock_wandb():
    """Mock wandb calls for testing"""
    with patch('wandb.init') as mock_init, \
         patch('wandb.log') as mock_log:
        mock_init.return_value = MagicMock(__enter__=MagicMock(), __exit__=MagicMock())
        yield mock_init, mock_log 