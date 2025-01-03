import pytest
from datetime import datetime
from models.message import Message

def test_message_creation():
    """Test creating a Message instance"""
    content = "Hello, world!"
    message = Message(role="user", content=content)
    
    assert message.role == "user"
    assert message.content == content
    assert message.name is None
    assert isinstance(message.attributes, dict)
    assert isinstance(message.timestamp, datetime)

def test_message_with_function_call():
    """Test creating a Message instance with function call"""
    function_call = {"name": "test_function", "arguments": "{}"}
    message = Message(
        role="assistant",
        content="",
        function_call=function_call
    )
    
    assert message.role == "assistant"
    assert message.function_call == function_call 