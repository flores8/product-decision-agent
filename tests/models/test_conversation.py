import pytest
from datetime import datetime
from models.conversation import Conversation, Message

def test_message_creation():
    """Test creating a Message instance"""
    content = "Hello, world!"
    message = Message(role="user", content=content)
    
    assert message.role == "user"
    assert message.content == content
    assert message.name is None
    assert message.function_call is None
    assert isinstance(message.metadata, dict)
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

def test_conversation_creation():
    """Test creating a Conversation instance"""
    conv_id = "test-conv-1"
    title = "Test Conversation"
    conversation = Conversation(id=conv_id, title=title)
    
    assert conversation.id == conv_id
    assert conversation.title == title
    assert len(conversation.messages) == 0
    assert isinstance(conversation.created_at, datetime)
    assert isinstance(conversation.updated_at, datetime)
    assert isinstance(conversation.metadata, dict)

def test_add_message():
    """Test adding a message to conversation"""
    conversation = Conversation(id="test-conv-2", title="Test")
    message = Message(role="user", content="Hello")
    
    conversation.add_message(message)
    
    assert len(conversation.messages) == 1
    assert conversation.messages[0] == message

def test_get_messages_for_chat_completion():
    """Test getting messages in chat completion format"""
    conversation = Conversation(id="test-conv-3", title="Test")
    
    # Add regular message
    msg1 = Message(role="user", content="Hello")
    conversation.add_message(msg1)
    
    # Add function message
    msg2 = Message(
        role="function",
        content="Function result",
        name="test_function"
    )
    conversation.add_message(msg2)
    
    # Add message with function call
    msg3 = Message(
        role="assistant",
        content="",
        function_call={"name": "test_function", "arguments": "{}"}
    )
    conversation.add_message(msg3)
    
    api_messages = conversation.get_messages_for_chat_completion()
    
    assert len(api_messages) == 3
    
    # Check regular message
    assert api_messages[0] == {
        "role": "user",
        "content": "Hello"
    }
    
    # Check function message
    assert api_messages[1] == {
        "role": "function",
        "content": "Function result",
        "name": "test_function"
    }
    
    # Check function call message
    assert api_messages[2] == {
        "role": "assistant",
        "content": "",
        "function_call": {"name": "test_function", "arguments": "{}"}
    }

def test_clear_messages():
    """Test clearing all messages from conversation"""
    conversation = Conversation(id="test-conv-4", title="Test")
    
    # Add some messages
    conversation.add_message(Message(role="user", content="Hello"))
    conversation.add_message(Message(role="assistant", content="Hi"))
    
    assert len(conversation.messages) == 2
    
    # Clear messages
    conversation.clear_messages()
    
    assert len(conversation.messages) == 0 