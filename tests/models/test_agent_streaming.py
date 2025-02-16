import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from tyler.models.agent import Agent
from tyler.models.thread import Thread
from tyler.models.message import Message


# Fake classes to simulate streaming responses
class FakeUsage:
    def __init__(self, completion_tokens, prompt_tokens, total_tokens):
        self.completion_tokens = completion_tokens
        self.prompt_tokens = prompt_tokens
        self.total_tokens = total_tokens

class FakeDelta:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

class FakeChoice:
    def __init__(self, delta, finish_reason):
        self.delta = delta
        self.finish_reason = finish_reason

class FakeChunk:
    def __init__(self, choices, usage=None):
        self.choices = choices
        self.usage = usage

# Fake streaming generator for no tool calls case
async def fake_streaming_no_tool_calls():
    # First chunk with partial content
    yield FakeChunk(choices=[FakeChoice(delta=FakeDelta(content="Hello, "), finish_reason="")])
    # Second chunk completes the message, with usage info
    yield FakeChunk(choices=[FakeChoice(delta=FakeDelta(content="world!"), finish_reason="stop")], 
                    usage=FakeUsage(completion_tokens=10, prompt_tokens=20, total_tokens=30))

# Fake streaming generator for tool calls case
async def fake_streaming_with_tool_calls():
    # First chunk with some content
    yield FakeChunk(choices=[FakeChoice(delta=FakeDelta(content="Output before tool call. "), finish_reason="")])
    # Second chunk with tool call info and usage
    tool_call = {
        "id": "tool_call_1",
        "type": "function",
        "function": {
            "name": "test_tool",
            "arguments": '{"arg": "value"}'
        }
    }
    yield FakeChunk(choices=[FakeChoice(delta=FakeDelta(content="", tool_calls=[tool_call]), finish_reason="tool_calls")], 
                    usage=FakeUsage(completion_tokens=5, prompt_tokens=15, total_tokens=20))

# Dummy object to simulate the weave call info
class DummyCall:
    id = "dummy-id"
    ui_url = "http://dummy-url"

@pytest.fixture
def dummy_thread():
    # Create a dummy thread with a single user message
    thread = Thread(id="test-thread", title="Test Thread")
    thread.add_message(Message(role="user", content="Test"))
    return thread


@pytest.mark.asyncio
async def test_streaming_no_tool_calls(dummy_thread):
    # Create an Agent with streaming enabled
    agent = Agent(stream=True, model_name="gpt-4o")
    
    # Create a mock for _get_completion that returns our fake streaming generator
    mock_get_completion = AsyncMock()
    mock_get_completion.call = AsyncMock(return_value=(fake_streaming_no_tool_calls(), DummyCall()))
    
    # Patch the _get_completion method
    with patch.object(agent, '_get_completion', mock_get_completion):
        # Call go
        thread, new_messages = await agent.go(dummy_thread)

        # There should be an assistant message added
        assistant_msgs = [msg for msg in thread.messages if msg.role == "assistant"]
        assert len(assistant_msgs) == 1
        assistant_msg = assistant_msgs[0]

        # Verify that the combined content is as expected
        expected_content = "Hello, world!"
        assert assistant_msg.content == expected_content
        
        # Verify that there are no tool calls
        assert assistant_msg.tool_calls is None or assistant_msg.tool_calls == []

        # Verify usage metrics in the assistant message
        usage = assistant_msg.metrics.get("usage", {})
        assert usage.get("completion_tokens") == 10
        assert usage.get("prompt_tokens") == 20
        assert usage.get("total_tokens") == 30


@pytest.mark.asyncio
async def test_streaming_with_tool_calls(dummy_thread):
    # Create an Agent with streaming enabled
    agent = Agent(stream=True, model_name="gpt-4o")
    
    # Create a mock for _get_completion that returns our fake streaming generator
    mock_get_completion = AsyncMock()
    mock_get_completion.call = AsyncMock(return_value=(fake_streaming_with_tool_calls(), DummyCall()))
    
    # Patch the _get_completion method
    with patch.object(agent, '_get_completion', mock_get_completion):
        # Call go
        thread, new_messages = await agent.go(dummy_thread)

        # There should be an assistant message added
        assistant_msgs = [msg for msg in thread.messages if msg.role == "assistant"]
        assert len(assistant_msgs) == 1
        assistant_msg = assistant_msgs[0]

        # Verify that the combined content is as expected
        expected_content = "Output before tool call. "
        assert assistant_msg.content == expected_content

        # Verify that the tool call was captured
        tool_calls = assistant_msg.tool_calls
        assert tool_calls is not None
        assert isinstance(tool_calls, list)
        assert len(tool_calls) == 1
        call = tool_calls[0]
        assert call["id"] == "tool_call_1"
        assert call["type"] == "function"
        assert call["function"]["name"] == "test_tool"
        assert call["function"]["arguments"] == '{"arg": "value"}'
        
        # Verify usage metrics in the assistant message
        usage = assistant_msg.metrics.get("usage", {})
        assert usage.get("completion_tokens") == 5
        assert usage.get("prompt_tokens") == 15
        assert usage.get("total_tokens") == 20 