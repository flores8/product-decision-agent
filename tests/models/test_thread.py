import pytest
from datetime import datetime, UTC
from tyler.models.thread import Thread
from tyler.models.message import Message

def test_create_thread():
    """Test creating a new thread"""
    thread = Thread(id="test-thread", title="Test Thread")
    assert thread.id == "test-thread"
    assert thread.title == "Test Thread"
    assert isinstance(thread.created_at, datetime)
    assert thread.created_at.tzinfo == UTC
    assert isinstance(thread.updated_at, datetime)
    assert thread.updated_at.tzinfo == UTC
    assert thread.messages == []
    assert thread.attributes == {}
    assert thread.source is None

def test_add_message():
    """Test adding a message to a thread"""
    thread = Thread(id="test-thread")
    message = Message(role="user", content="Hello")
    thread.add_message(message)
    assert len(thread.messages) == 1
    assert thread.messages[0].role == "user"
    assert thread.messages[0].content == "Hello"
    assert thread.messages[0].sequence == 0
    assert thread.title == "Hello"  # Title should be set from first user message

def test_thread_serialization():
    """Test thread serialization to/from dict"""
    thread = Thread(
        id="test-thread",
        title="Test Thread",
        attributes={"category": "test"},
        source={"name": "slack", "channel": "general"}
    )
    thread.add_message(Message(role="user", content="Hello"))
    
    # Test to_dict()
    data = thread.to_dict()
    assert data["id"] == "test-thread"
    assert data["title"] == "Test Thread"
    assert data["attributes"] == {"category": "test"}
    assert data["source"] == {"name": "slack", "channel": "general"}
    assert len(data["messages"]) == 1
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Hello"
    assert isinstance(data["created_at"], str)
    assert isinstance(data["updated_at"], str)
    
    # Test model_dump() and model_validate()
    data = thread.model_dump()
    new_thread = Thread.model_validate(data)
    assert new_thread.id == thread.id
    assert new_thread.title == thread.title
    assert new_thread.attributes == thread.attributes
    assert new_thread.source == thread.source
    assert len(new_thread.messages) == len(thread.messages)
    assert new_thread.messages[0].role == thread.messages[0].role
    assert new_thread.messages[0].content == thread.messages[0].content

def test_get_messages_for_chat_completion():
    """Test getting messages in chat completion format"""
    thread = Thread(id="test-thread")
    thread.add_message(Message(role="system", content="You are a helpful assistant"))
    thread.add_message(Message(role="user", content="Hello"))
    thread.add_message(Message(role="assistant", content="Hi there!"))
    
    messages = thread.get_messages_for_chat_completion()
    assert len(messages) == 3
    assert messages[0] == {"role": "system", "content": "You are a helpful assistant"}
    assert messages[1] == {"role": "user", "content": "Hello"}
    assert messages[2] == {"role": "assistant", "content": "Hi there!"}

def test_ensure_system_prompt():
    """Test ensuring system prompt exists"""
    thread = Thread(id="test-thread")
    thread.add_message(Message(role="user", content="Hello"))
    
    # Add system prompt
    thread.ensure_system_prompt("You are a helpful assistant")
    assert len(thread.messages) == 2
    assert thread.messages[0].role == "system"
    assert thread.messages[0].content == "You are a helpful assistant"
    assert thread.messages[1].role == "user"
    
    # Try adding again - should not duplicate
    thread.ensure_system_prompt("You are a helpful assistant")
    assert len(thread.messages) == 2  # No change
    assert thread.messages[0].role == "system" 