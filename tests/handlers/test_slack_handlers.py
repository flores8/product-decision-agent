import pytest
from unittest.mock import patch, MagicMock, create_autospec, call, Mock, NonCallableMagicMock
from handlers.slack_handlers import SlackEventHandler
from tools.slack import SlackClient
from models.TylerAgent import TylerAgent
from models.conversation import Conversation
from models.message import Message
from database.conversation_store import ConversationStore

@pytest.fixture
def mock_slack_client():
    mock = MagicMock(spec=SlackClient)
    # Create nested mock for client.chat_postMessage
    mock.client = MagicMock()
    mock.client.chat_postMessage = MagicMock(return_value={"ok": True})
    return mock

@pytest.fixture
def mock_tyler_agent():
    """Create a strictly spec'd mock of TylerAgent to ensure we're not executing real Tyler code"""
    mock = create_autospec(TylerAgent, instance=True, spec_set=True)
    # Set up the go method to return immediately
    mock.go.return_value = None
    return mock

@pytest.fixture
def mock_conversation_store():
    return MagicMock(spec=ConversationStore)

@pytest.fixture
def handler(mock_slack_client, mock_tyler_agent, mock_conversation_store):
    return SlackEventHandler(
        slack_client=mock_slack_client,
        tyler_agent=mock_tyler_agent,
        conversation_store=mock_conversation_store
    )

def test_handle_mention_new_conversation(handler, mock_conversation_store, mock_tyler_agent):
    """Test handling a mention that creates a new conversation"""
    # Setup
    event_data = {
        'channel': 'C123',
        'thread_ts': '1234567890.123',
        'user': 'U123',
        'text': 'Hey Tyler, how are you?'
    }
    mock_conversation_store.get.side_effect = [None, None]  # Return None for both get() calls
    mock_conversation = None

    def save_conversation(conv):
        nonlocal mock_conversation
        mock_conversation = conv
        return True

    mock_conversation_store.save.side_effect = save_conversation

    # Execute
    handler.handle_mention(event_data)

    # Verify
    assert mock_conversation_store.get.call_count == 2
    assert mock_conversation_store.get.call_args_list[0] == call('slack-C123-1234567890.123')
    assert mock_conversation_store.get.call_args_list[1] == call('slack-C123-1234567890.123')
    
    # Verify conversation creation
    assert mock_conversation is not None
    assert mock_conversation.id == 'slack-C123-1234567890.123'
    assert mock_conversation.title == 'Hey Tyler, how are you?'
    
    # Verify message was added
    messages = mock_conversation.messages
    assert len(messages) == 1
    assert messages[0].role == 'user'
    assert messages[0].content == 'Hey Tyler, how are you?'
    assert messages[0].attributes['slack_user'] == 'U123'

    # Verify Tyler agent was triggered with mock
    mock_tyler_agent.go.assert_called_once_with('slack-C123-1234567890.123')
    # Verify we're using the mock and not a real instance
    assert isinstance(handler.tyler_agent, NonCallableMagicMock)

def test_handle_mention_existing_conversation(handler, mock_conversation_store, mock_tyler_agent):
    """Test handling a mention in an existing conversation"""
    # Setup
    event_data = {
        'channel': 'C123',
        'thread_ts': '1234567890.123',
        'user': 'U123',
        'text': 'Another message'
    }
    
    existing_conversation = Conversation(
        id='slack-C123-1234567890.123',
        title='Existing Conversation'
    )
    mock_conversation_store.get.side_effect = [existing_conversation, existing_conversation]

    # Execute
    handler.handle_mention(event_data)

    # Verify
    assert mock_conversation_store.get.call_count == 2
    assert mock_conversation_store.get.call_args_list[0] == call('slack-C123-1234567890.123')
    assert mock_conversation_store.get.call_args_list[1] == call('slack-C123-1234567890.123')
    
    # Verify message was added to existing conversation
    messages = existing_conversation.messages
    assert len(messages) == 1
    assert messages[0].role == 'user'
    assert messages[0].content == 'Another message'
    assert messages[0].attributes['slack_user'] == 'U123'

    # Verify Tyler agent was triggered with mock
    mock_tyler_agent.go.assert_called_once_with('slack-C123-1234567890.123')
    # Verify we're using the mock and not a real instance
    assert isinstance(handler.tyler_agent, NonCallableMagicMock)

def test_handle_mention_with_response(handler, mock_conversation_store, mock_tyler_agent):
    """Test handling a mention and sending Tyler's response"""
    # Setup
    event_data = {
        'channel': 'C123',
        'thread_ts': '1234567890.123',
        'user': 'U123',
        'text': 'Hello Tyler'
    }
    
    conversation = Conversation(
        id='slack-C123-1234567890.123',
        title='Test Conversation'
    )
    mock_conversation_store.get.side_effect = [conversation, conversation]  # For initial get and after processing
    
    # Add Tyler's response to the conversation
    conversation.add_message(Message(
        role='assistant',
        content='Hello! How can I help you today?'
    ))

    # Execute
    handler.handle_mention(event_data)

    # Verify Tyler agent was triggered with mock
    mock_tyler_agent.go.assert_called_once_with('slack-C123-1234567890.123')
    # Verify we're using the mock and not a real instance
    assert isinstance(handler.tyler_agent, NonCallableMagicMock)

    # Verify response was sent to Slack
    handler.slack_client.client.chat_postMessage.assert_called_with(
        channel='C123',
        thread_ts='1234567890.123',
        text='Hello! How can I help you today?'
    )

def test_handle_mention_error_handling(handler, mock_tyler_agent):
    """Test error handling in handle_mention"""
    # Setup
    event_data = {
        'channel': 'C123',
        'thread_ts': '1234567890.123',
        'user': 'U123',
        'text': 'Hello Tyler'
    }
    
    # Simulate an error in conversation store
    handler.conversation_store.get.side_effect = Exception("Database error")

    # Execute
    handler.handle_mention(event_data)

    # Verify Tyler agent was never called due to error
    mock_tyler_agent.go.assert_not_called()
    # Verify we're using the mock and not a real instance
    assert isinstance(handler.tyler_agent, NonCallableMagicMock)

    # Verify error message was sent to Slack
    handler.slack_client.client.chat_postMessage.assert_called_with(
        channel='C123',
        thread_ts='1234567890.123',
        text='Sorry, I encountered an error: Database error'
    )

def test_handle_mention_with_parent_thread(handler, mock_conversation_store, mock_tyler_agent):
    """Test handling a mention that references a parent thread"""
    # Setup
    event_data = {
        'channel': 'C123',
        'ts': '1234567890.456',  # Reply timestamp
        'thread_ts': '1234567890.123',  # Parent thread timestamp
        'user': 'U123',
        'text': 'Follow-up question'
    }
    
    conversation = Conversation(
        id='slack-C123-1234567890.123',  # Should use parent thread ts
        title='Test Conversation'
    )
    mock_conversation_store.get.side_effect = [conversation, conversation]

    # Execute
    handler.handle_mention(event_data)

    # Verify correct conversation ID was used
    assert mock_conversation_store.get.call_count == 2
    assert mock_conversation_store.get.call_args_list[0] == call('slack-C123-1234567890.123')
    assert mock_conversation_store.get.call_args_list[1] == call('slack-C123-1234567890.123')
    
    # Verify message was added
    messages = conversation.messages
    assert len(messages) == 1
    assert messages[0].content == 'Follow-up question'

    # Verify Tyler agent was triggered with mock
    mock_tyler_agent.go.assert_called_once_with('slack-C123-1234567890.123')
    # Verify we're using the mock and not a real instance
    assert isinstance(handler.tyler_agent, NonCallableMagicMock) 