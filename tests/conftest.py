import pytest
import os
from unittest.mock import patch

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