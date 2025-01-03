import pytest
from datetime import datetime
from models.conversation import Conversation
from models.message import Message

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
    assert isinstance(conversation.attributes, dict)

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
    
    api_messages = conversation.get_messages_for_chat_completion()
    
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
    """Test clearing all messages from conversation"""
    conversation = Conversation(id="test-conv-4", title="Test")
    
    # Add some messages
    conversation.add_message(Message(role="user", content="Hello"))
    conversation.add_message(Message(role="assistant", content="Hi"))
    
    assert len(conversation.messages) == 2
    
    # Clear messages
    conversation.clear_messages()
    
    assert len(conversation.messages) == 0

def test_ensure_system_prompt():
    """Test ensuring system prompt is present and correct"""
    conversation = Conversation(id="test-conv-5", title="Test")
    prompt = "System prompt"
    
    # Test adding system prompt to empty conversation
    conversation.ensure_system_prompt(prompt)
    assert len(conversation.messages) == 1
    assert conversation.messages[0].role == "system"
    assert conversation.messages[0].content == prompt
    
    # Test updating existing system prompt
    new_prompt = "New system prompt"
    conversation.ensure_system_prompt(new_prompt)
    assert len(conversation.messages) == 1
    assert conversation.messages[0].role == "system"
    assert conversation.messages[0].content == new_prompt
    
    # Test adding system prompt when other messages exist
    conversation.add_message(Message(role="user", content="Hello"))
    another_prompt = "Another system prompt"
    conversation.ensure_system_prompt(another_prompt)
    assert len(conversation.messages) == 2
    assert conversation.messages[0].role == "system"
    assert conversation.messages[0].content == another_prompt 