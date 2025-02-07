import pytest
from unittest.mock import patch, MagicMock, create_autospec, AsyncMock
from tyler.models.router_agent import RouterAgent, RouterAgentPrompt
from tyler.models.registry import Registry
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.database.thread_store import ThreadStore
from datetime import datetime

pytest_plugins = ('pytest_asyncio',)

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

@pytest.fixture
def mock_registry():
    """Create a mock registry that inherits from Registry"""
    registry = Registry()
    registry.list_agents = MagicMock(return_value=["agent1", "agent2"])
    registry.has_agent = MagicMock(side_effect=lambda x: x in ["agent1", "agent2"])
    registry.get_agent = MagicMock()
    return registry

@pytest.fixture
def mock_thread_store():
    """Create a mock thread store that inherits from ThreadStore"""
    store = ThreadStore()
    store.get = AsyncMock()  # Use AsyncMock for async methods
    return store

@pytest.fixture
def mock_prompt():
    mock = create_autospec(RouterAgentPrompt, instance=True)
    mock.system_prompt.return_value = "Test system prompt"
    return mock

@pytest.fixture
def router_agent(mock_thread_store, mock_registry):
    """Create a router agent with mocked dependencies"""
    return RouterAgent(
        thread_store=mock_thread_store,
        registry=mock_registry
    )

def test_init(router_agent):
    """Test RouterAgent initialization"""
    assert isinstance(router_agent.registry, Registry)
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

@pytest.mark.asyncio
async def test_route_thread_not_found(router_agent, mock_thread_store):
    """Test routing when thread is not found"""
    mock_thread_store.get.return_value = None
    result = await router_agent.route("nonexistent-thread")
    assert result is None
    mock_thread_store.get.assert_called_once_with("nonexistent-thread")

@pytest.mark.asyncio
async def test_route_no_user_message(router_agent, mock_thread_store):
    """Test routing when there are no user messages in thread"""
    thread = Thread(id="test-thread", title="Test Thread")
    thread.messages = [
        Message(role="assistant", content="Hi!")
    ]
    mock_thread_store.get.return_value = thread
    result = await router_agent.route("test-thread")
    assert result is None

@pytest.mark.asyncio
async def test_route_with_mention(router_agent, mock_thread_store, mock_registry):
    """Test routing with explicit @mention"""
    thread = Thread(id="test-thread", title="Test Thread")
    thread.messages = [
        Message(role="user", content="Hey @agent1, help me")
    ]
    mock_thread_store.get.return_value = thread
    mock_registry.get_agent.return_value = True
    
    result = await router_agent.route("test-thread")
    assert result == "agent1"
    mock_registry.get_agent.assert_called_once_with("agent1")

def test_prompt_system_prompt(mock_registry):
    """Test RouterAgentPrompt system prompt generation"""
    prompt = RouterAgentPrompt()
    agent_descriptions = "agent1: purpose1\nagent2: purpose2"
    
    system_prompt = prompt.system_prompt(agent_descriptions)
    
    assert "You are a router agent" in system_prompt
    assert agent_descriptions in system_prompt
    assert datetime.now().strftime("%Y-%m-%d") in system_prompt 