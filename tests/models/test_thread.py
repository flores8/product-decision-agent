import pytest
from datetime import datetime
from models.Thread import Thread
from models.message import Message

def test_thread_creation():
    """Test creating a Thread instance"""
    thread_id = "test-thread-1"
    title = "Test Thread"
    thread = Thread(id=thread_id, title=title)
    
    assert thread.id == thread_id
    assert thread.title == title
    assert len(thread.messages) == 0
    assert isinstance(thread.created_at, datetime)
    assert isinstance(thread.updated_at, datetime)
    assert isinstance(thread.attributes, dict)

def test_add_message():
    """Test adding a message to thread"""
    thread = Thread(id="test-thread-2", title="Test")
    message = Message(role="user", content="Hello")
    
    thread.add_message(message)
    
    assert len(thread.messages) == 1
    assert thread.messages[0] == message

def test_get_messages_for_chat_completion():
    """Test getting messages in chat completion format"""
    thread = Thread(id="test-thread-3", title="Test")
    
    # Add regular message
    msg1 = Message(role="user", content="Hello")
    thread.add_message(msg1)
    
    # Add function message
    msg2 = Message(
        role="function",
        content="Function result",
        name="test_function"
    )
    thread.add_message(msg2)
    
    api_messages = thread.get_messages_for_chat_completion()
    
    assert len(api_messages) == 2
    
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

def test_clear_messages():
    """Test clearing all messages from thread"""
    thread = Thread(id="test-thread-4", title="Test")
    
    # Add some messages
    thread.add_message(Message(role="user", content="Hello"))
    thread.add_message(Message(role="assistant", content="Hi"))
    
    assert len(thread.messages) == 2
    
    # Clear messages
    thread.clear_messages()
    
    assert len(thread.messages) == 0

def test_ensure_system_prompt():
    """Test ensuring system prompt is present and correct"""
    thread = Thread(id="test-thread-5", title="Test")
    prompt = "System prompt"
    
    # Test adding system prompt to empty thread
    thread.ensure_system_prompt(prompt)
    assert len(thread.messages) == 1
    assert thread.messages[0].role == "system"
    assert thread.messages[0].content == prompt
    
    # Test updating existing system prompt
    new_prompt = "New system prompt"
    thread.ensure_system_prompt(new_prompt)
    assert len(thread.messages) == 1
    assert thread.messages[0].role == "system"
    assert thread.messages[0].content == new_prompt
    
    # Test adding system prompt when other messages exist
    thread.add_message(Message(role="user", content="Hello"))
    another_prompt = "Another system prompt"
    thread.ensure_system_prompt(another_prompt)
    assert len(thread.messages) == 2
    assert thread.messages[0].role == "system"
    assert thread.messages[0].content == another_prompt 