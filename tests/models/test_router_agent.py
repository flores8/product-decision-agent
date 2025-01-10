import pytest
from unittest.mock import patch, MagicMock, create_autospec
from models.router_agent import RouterAgent, RouterAgentPrompt
from models.registry import Registry
from models.thread import Thread
from models.message import Message
from database.thread_store import ThreadStore
from datetime import datetime

@pytest.fixture
def mock_registry():
    registry = create_autospec(Registry, instance=True)
    registry.list_agents.return_value = ["agent1", "agent2"]
    registry.has_agent.side_effect = lambda x: x in ["agent1", "agent2"]
    registry.get_agent.side_effect = lambda x: MagicMock(purpose="Test purpose") if x in ["agent1", "agent2"] else None
    return registry

@pytest.fixture
def mock_thread_store():
    return create_autospec(ThreadStore, instance=True)

@pytest.fixture
def mock_prompt():
    mock = create_autospec(RouterAgentPrompt, instance=True)
    mock.system_prompt.return_value = "Test system prompt"
    return mock

@pytest.fixture
def router_agent(mock_registry, mock_thread_store, mock_prompt):
    return RouterAgent(
        registry=mock_registry,
        model_name="gpt-4",
        prompt=mock_prompt,
        thread_store=mock_thread_store
    )

def test_init(router_agent):
    """Test RouterAgent initialization"""
    assert router_agent.model_name == "gpt-4"
    assert isinstance(router_agent.registry, Registry)
    assert isinstance(router_agent.prompt, RouterAgentPrompt)
    assert isinstance(router_agent.thread_store, ThreadStore)

def test_extract_mentions(router_agent):
    """Test extracting @mentions from text"""
    # Test simple text
    text = "Hello @agent1 and @agent2"
    mentions = router_agent._extract_mentions(text)
    assert mentions == ["agent1", "agent2"]
    
    # Test multimodal content
    multimodal = [{"text": "Hello @agent1 and @agent2", "type": "text"}]
    mentions = router_agent._extract_mentions(multimodal)
    assert mentions == ["agent1", "agent2"]
    
    # Test no mentions
    text = "Hello there"
    mentions = router_agent._extract_mentions(text)
    assert mentions == []

def test_route_thread_not_found(router_agent, mock_thread_store):
    """Test routing when thread is not found"""
    mock_thread_store.get.return_value = None
    result = router_agent.route("nonexistent-thread")
    assert result is None

def test_route_no_user_message(router_agent, mock_thread_store):
    """Test routing when there are no user messages in thread"""
    thread = Thread(id="test-thread", title="Test Thread")
    thread.messages = [
        Message(role="assistant", content="Hi!")
    ]
    mock_thread_store.get.return_value = thread
    
    result = router_agent.route("test-thread")
    assert result is None

def test_route_with_mention(router_agent, mock_thread_store, mock_registry):
    """Test routing with explicit @mention"""
    thread = Thread(id="test-thread", title="Test Thread")
    thread.messages = [
        Message(role="user", content="Hey @agent1, help me")
    ]
    mock_thread_store.get.return_value = thread
    
    result = router_agent.route("test-thread")
    assert result == "agent1"
    # Verify completion API wasn't called since mention was found
    assert not any(call.args[0] == "completion" for call in mock_registry.mock_calls)

def test_prompt_system_prompt(mock_registry):
    """Test RouterAgentPrompt system prompt generation"""
    prompt = RouterAgentPrompt()
    agent_descriptions = "agent1: purpose1\nagent2: purpose2"
    
    system_prompt = prompt.system_prompt(agent_descriptions)
    
    assert "You are a router agent" in system_prompt
    assert agent_descriptions in system_prompt
    assert datetime.now().strftime("%Y-%m-%d") in system_prompt 