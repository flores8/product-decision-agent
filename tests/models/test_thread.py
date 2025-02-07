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
    assert thread.messages[0].sequence == 1

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
    assert messages[0] == {
        "role": "system",
        "content": "You are a helpful assistant",
        "sequence": 0
    }
    assert messages[1] == {
        "role": "user",
        "content": "Hello",
        "sequence": 1
    }
    assert messages[2] == {
        "role": "assistant",
        "content": "Hi there!",
        "sequence": 2
    }

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

def test_message_sequencing():
    """Test message sequence numbering"""
    thread = Thread(id="test-thread")
    
    # Add messages in different order
    msg1 = Message(role="user", content="First user message")
    msg2 = Message(role="assistant", content="First assistant message")
    msg3 = Message(role="system", content="System message")
    msg4 = Message(role="user", content="Second user message")
    
    thread.add_message(msg1)  # Should get sequence 1
    thread.add_message(msg2)  # Should get sequence 2
    thread.add_message(msg3)  # Should get sequence 0 and move to front
    thread.add_message(msg4)  # Should get sequence 3
    
    # Verify sequences
    assert len(thread.messages) == 4
    assert thread.messages[0].role == "system"
    assert thread.messages[0].sequence == 0
    
    # Get non-system messages in order
    non_system = [m for m in thread.messages if m.role != "system"]
    assert len(non_system) == 3
    assert non_system[0].content == "First user message"
    assert non_system[0].sequence == 1
    assert non_system[1].content == "First assistant message"
    assert non_system[1].sequence == 2
    assert non_system[2].content == "Second user message"
    assert non_system[2].sequence == 3 