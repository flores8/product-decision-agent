import pytest
from datetime import datetime
from models.Message import Message

def test_message_creation():
    """Test creating a Message instance"""
    content = "Hello, world!"
    message = Message(role="user", content=content)
    
    assert message.role == "user"
    assert message.content == content
    assert message.name is None
    assert isinstance(message.attributes, dict)
    assert isinstance(message.timestamp, datetime) 