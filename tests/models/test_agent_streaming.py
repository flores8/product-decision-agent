import pytest
from unittest.mock import patch, MagicMock, AsyncMock, create_autospec
from tyler.models.agent import Agent, StreamUpdate
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.utils.tool_runner import tool_runner
from litellm import ModelResponse
import json
from types import SimpleNamespace

def create_streaming_chunk(content=None, tool_calls=None, role="assistant", usage=None):
    """Helper function to create streaming chunks with proper structure"""
    delta = {"role": role}
    if content is not None:
        delta["content"] = content
    if tool_calls is not None:
        delta["tool_calls"] = tool_calls
    delta_obj = SimpleNamespace(**delta)
    chunk = {
        "id": "chunk-id",
        "choices": [{
            "index": 0,
            "delta": delta_obj
        }]
    }
    if usage:
        chunk["usage"] = usage
    return ModelResponse(**chunk)

@pytest.fixture
def mock_litellm():
    mock = AsyncMock()
    mock.return_value = ModelResponse(**{
        "id": "test-id",
        "choices": [{
            "finish_reason": "stop",
            "index": 0,
            "message": {
                "content": "Test response",
                "role": "assistant",
                "tool_calls": None
            }
        }],
        "model": "gpt-4",
        "usage": {
            "completion_tokens": 10,
            "prompt_tokens": 20,
            "total_tokens": 30
        }
    })
    
    with patch('litellm.acompletion', mock), \
         patch('tyler.models.agent.acompletion', mock):
        yield mock

@pytest.fixture
def agent(mock_litellm):
    with patch('tyler.models.agent.tool_runner', create_autospec(tool_runner)):
        agent = Agent(
            model_name="gpt-4o",
            temperature=0.7,
            purpose="test purpose",
            stream=True
        )
        # Mock the weave operation
        mock_get_completion = AsyncMock()
        mock_get_completion.call = AsyncMock()
        agent._get_completion = mock_get_completion
        return agent

@pytest.mark.asyncio
async def test_process_streaming_chunks_content_only():
    """Test processing streaming chunks with only content (no tool calls)"""
    agent = Agent(stream=True)
    
    # Create mock chunks with only content
    chunks = [
        create_streaming_chunk(content="Hello"),
        create_streaming_chunk(content=" world"),
        create_streaming_chunk(content="!", usage={
            "completion_tokens": 10,
            "prompt_tokens": 20,
            "total_tokens": 30
        })
    ]
    
    async def mock_chunks():
        for chunk in chunks:
            yield chunk
    
    pre_tool, post_tool, tool_calls, usage = await agent._process_streaming_chunks(mock_chunks())
    
    # Verify content is accumulated correctly
    assert pre_tool == "Hello world!"
    assert post_tool == ""  # No post-tool content
    assert not tool_calls  # No tool calls
    assert usage == {
        "completion_tokens": 10,
        "prompt_tokens": 20,
        "total_tokens": 30
    }

@pytest.mark.asyncio
async def test_process_streaming_chunks_with_tool_calls():
    """Test processing streaming chunks with tool calls"""
    agent = Agent(stream=True)
    
    # Create mock chunks with tool calls split across two chunks for JSON concatenation
    chunks = [
        create_streaming_chunk(content="Let me help you with that."),
        create_streaming_chunk(tool_calls=[{
            "id": "call_123",
            "type": "function",
            "function": {"name": "translate", "arguments": "{\"text\": \"hello\","}
        }]),
        create_streaming_chunk(tool_calls=[{
            "function": {"arguments": " \"target_language\": \"Spanish\"}"}
        }]),
        create_streaming_chunk(content="Here's the translation:", usage={
            "completion_tokens": 15,
            "prompt_tokens": 25,
            "total_tokens": 40
        })
    ]
    
    async def mock_chunks():
        for chunk in chunks:
            yield chunk
    
    pre_tool, post_tool, tool_calls, usage = await agent._process_streaming_chunks(mock_chunks())
    
    # Verify content and tool calls
    assert pre_tool == "Let me help you with that."
    assert post_tool == "Here's the translation:"
    assert len(tool_calls) == 1
    assert tool_calls[0]["id"] == "call_123"
    assert tool_calls[0]["type"] == "function"
    assert tool_calls[0]["function"]["name"] == "translate"
    # The tool_calls argument should be a valid JSON string
    args = tool_calls[0]["function"]["arguments"]
    parsed_args = json.loads(args)
    assert parsed_args == {
        "text": "hello",
        "target_language": "Spanish"
    }
    assert usage == {
        "completion_tokens": 15,
        "prompt_tokens": 25,
        "total_tokens": 40
    }

@pytest.mark.asyncio
async def async_generator(chunks):
    for chunk in chunks:
        yield chunk

@pytest.mark.asyncio
async def test_go_stream_basic_response():
    """Test streaming with basic response (no tool calls)"""
    agent = Agent(stream=True)
    thread = Thread()
    thread.add_message(Message(role="user", content="Hello"))
    
    # Mock the completion response
    chunks = [
        create_streaming_chunk(content="Hello"),
        create_streaming_chunk(content=" there!")
    ]
    
    mock_weave_call = MagicMock()
    mock_weave_call.id = "test-weave-id"
    
    with patch.object(agent, '_get_completion') as mock_get_completion:
        mock_get_completion.call.return_value = (async_generator(chunks), mock_weave_call)
        
        updates = []
        async for update in agent.go_stream(thread):
            updates.append(update)
        
        # Verify the updates
        assert len(updates) >= 3  # At least content chunks and complete
        assert any(update.type == StreamUpdate.Type.CONTENT_CHUNK and update.data == "Hello" for update in updates)
        assert any(update.type == StreamUpdate.Type.CONTENT_CHUNK and update.data == " there!" for update in updates)
        assert any(update.type == StreamUpdate.Type.ASSISTANT_MESSAGE for update in updates)
        assert any(update.type == StreamUpdate.Type.COMPLETE for update in updates)

@pytest.mark.asyncio
async def test_go_stream_with_tool_calls():
    """Test streaming with tool calls"""
    agent = Agent(stream=True)
    thread = Thread()
    thread.add_message(Message(role="user", content="Translate 'hello' to Spanish"))
    
    # Mock the completion response with tool calls
    chunks = [
        create_streaming_chunk(content="I'll help translate that."),
        create_streaming_chunk(tool_calls=[{
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "translate",
                "arguments": '{"text": "hello", "target_language": "Spanish"}'
            }
        }])
    ]
    
    mock_weave_call = MagicMock()
    mock_weave_call.id = "test-weave-id"
    
    with patch.object(agent, '_get_completion') as mock_get_completion, \
         patch('tyler.models.agent.tool_runner') as mock_tool_runner:
        mock_get_completion.call.return_value = (async_generator(chunks), mock_weave_call)
        mock_tool_runner.execute_tool_call = AsyncMock(return_value={
            "name": "translate",
            "content": "Translation: hola"
        })
        
        updates = []
        async for update in agent.go_stream(thread):
            updates.append(update)
        
        # Verify the updates
        assert len(updates) >= 4  # At least content chunk, tool message, and complete
        assert any(update.type == StreamUpdate.Type.CONTENT_CHUNK and 
                  update.data == "I'll help translate that." for update in updates)
        assert any(update.type == StreamUpdate.Type.TOOL_MESSAGE and 
                  update.data.content == "Translation: hola" for update in updates)
        assert any(update.type == StreamUpdate.Type.ASSISTANT_MESSAGE for update in updates)
        assert any(update.type == StreamUpdate.Type.COMPLETE for update in updates)

@pytest.mark.asyncio
async def test_go_stream_error_handling():
    """Test error handling in streaming"""
    agent = Agent(stream=True)
    thread = Thread()
    thread.add_message(Message(role="user", content="Test error handling"))

    # Mock the completion call to raise an error
    mock_completion = AsyncMock()
    mock_completion.call.side_effect = Exception("API Error")
    agent._get_completion = mock_completion

    # Mock the step method to return a streaming response
    async def mock_step(*args, **kwargs):
        raise Exception("API Error")
    
    with patch.object(agent, 'step', side_effect=mock_step):
        updates = []
        async for update in agent.go_stream(thread):
            updates.append(update)

        # Verify error update was sent
        error_updates = [update for update in updates if update.type == StreamUpdate.Type.ERROR]
        assert len(error_updates) == 1
        assert "API Error" in str(error_updates[0].data)

@pytest.mark.asyncio
async def test_go_stream_tool_execution_error():
    """Test handling of tool execution errors in streaming"""
    agent = Agent(stream=True)
    thread = Thread()
    thread.add_message(Message(role="user", content="Test tool error"))
    
    # Mock chunks with tool call
    chunks = [
        create_streaming_chunk(tool_calls=[{
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": '{}'
            }
        }])
    ]
    
    mock_weave_call = MagicMock()
    
    with patch.object(agent, '_get_completion') as mock_get_completion, \
         patch('tyler.models.agent.tool_runner') as mock_tool_runner:
        mock_get_completion.call.return_value = (async_generator(chunks), mock_weave_call)
        mock_tool_runner.execute_tool_call = AsyncMock(side_effect=Exception("Tool Error"))
        
        updates = []
        async for update in agent.go_stream(thread):
            updates.append(update)
        
        # Verify error handling
        assert any(update.type == StreamUpdate.Type.ERROR and 
                  "Tool Error" in str(update.data) for update in updates)

@pytest.mark.asyncio
async def test_go_stream_max_iterations():
    """Test handling of max iterations in streaming"""
    agent = Agent(stream=True, max_tool_iterations=1)  # Set to 1 to trigger quickly
    thread = Thread()
    thread.add_message(Message(role="user", content="Test max iterations"))
    
    # Mock chunks that will trigger tool calls
    chunks = [
        create_streaming_chunk(tool_calls=[{
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": '{}'
            }
        }])
    ]
    
    mock_weave_call = MagicMock()
    
    with patch.object(agent, '_get_completion') as mock_get_completion, \
         patch('tyler.models.agent.tool_runner') as mock_tool_runner:
        mock_get_completion.call.return_value = (async_generator(chunks), mock_weave_call)
        mock_tool_runner.execute_tool_call = AsyncMock(return_value={
            "name": "test_tool",
            "content": "Tool result"
        })
        
        updates = []
        async for update in agent.go_stream(thread):
            updates.append(update)
        
        # Verify max iterations message
        assert any(update.type == StreamUpdate.Type.ASSISTANT_MESSAGE and 
                  "Maximum tool iteration count reached" in update.data.content for update in updates)

@pytest.mark.asyncio
async def test_go_stream_invalid_json_handling():
    """Test handling of invalid JSON in tool arguments"""
    agent = Agent(stream=True)
    thread = Thread()
    thread.add_message(Message(role="user", content="Test invalid JSON"))
    
    # Mock chunks with invalid JSON in tool arguments
    chunks = [
        create_streaming_chunk(tool_calls=[{
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": '{"invalid": "json"'  # Missing closing brace
            }
        }])
    ]
    
    mock_weave_call = MagicMock()
    
    with patch.object(agent, '_get_completion') as mock_get_completion:
        mock_get_completion.call.return_value = (async_generator(chunks), mock_weave_call)
        
        updates = []
        async for update in agent.go_stream(thread):
            updates.append(update)
        
        # Verify error handling: Check for 'Tool execution failed:' substring in error message
        assert any(update.type == StreamUpdate.Type.ERROR and 
                  "Tool execution failed:" in str(update.data) for update in updates)

@pytest.mark.asyncio
async def test_go_stream_metrics_tracking():
    """Test that metrics are properly tracked in streaming mode"""
    agent = Agent(stream=True, model_name="gpt-4o")
    thread = Thread()
    thread.add_message(Message(role="user", content="Test metrics"))
    
    # Mock chunks with usage info
    chunks = [
        create_streaming_chunk(content="Hello"),
        create_streaming_chunk(content=" world", usage={
            "completion_tokens": 10,
            "prompt_tokens": 20,
            "total_tokens": 30
        })
    ]
    
    mock_weave_call = MagicMock()
    mock_weave_call.id = "test-weave-id"
    mock_weave_call.ui_url = "https://weave.ui/test"
    
    with patch.object(agent, '_get_completion') as mock_get_completion:
        mock_get_completion.call.return_value = (async_generator(chunks), mock_weave_call)
        
        updates = []
        async for update in agent.go_stream(thread):
            updates.append(update)
        
        # Find the assistant message update
        assistant_message = next(
            update.data for update in updates 
            if update.type == StreamUpdate.Type.ASSISTANT_MESSAGE
        )
        
        # Verify metrics are present and correct
        assert "metrics" in assistant_message.model_dump()
        assert assistant_message.metrics["model"] == "gpt-4o"
        assert "timing" in assistant_message.metrics
        assert "started_at" in assistant_message.metrics["timing"]
        assert "ended_at" in assistant_message.metrics["timing"]
        assert "latency" in assistant_message.metrics["timing"]
        assert assistant_message.metrics["usage"] == {
            "completion_tokens": 10,
            "prompt_tokens": 20,
            "total_tokens": 30
        }
        assert assistant_message.metrics["weave_call"]["id"] == "test-weave-id"
        assert assistant_message.metrics["weave_call"]["ui_url"] == "https://weave.ui/test"

@pytest.mark.asyncio
async def test_go_stream_tool_metrics():
    """Test that tool execution metrics are tracked in streaming mode"""
    agent = Agent(stream=True, model_name="gpt-4o")
    thread = Thread()
    thread.add_message(Message(role="user", content="Test tool metrics"))
    
    # Mock chunks with tool call
    chunks = [
        create_streaming_chunk(tool_calls=[{
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": '{}'
            }
        }])
    ]
    
    mock_weave_call = MagicMock()
    mock_weave_call.id = "test-weave-id"
    mock_weave_call.ui_url = "https://weave.ui/test"
    
    with patch.object(agent, '_get_completion') as mock_get_completion, \
         patch('tyler.models.agent.tool_runner') as mock_tool_runner:
        mock_get_completion.call.return_value = (async_generator(chunks), mock_weave_call)
        mock_tool_runner.execute_tool_call = AsyncMock(return_value={
            "name": "test_tool",
            "content": "Tool result"
        })
        
        updates = []
        async for update in agent.go_stream(thread):
            updates.append(update)
        
        # Find the tool message update
        tool_message = next(
            update.data for update in updates 
            if update.type == StreamUpdate.Type.TOOL_MESSAGE
        )
        
        # Verify tool metrics are present and correct with actual values
        assert "metrics" in tool_message.model_dump()
        assert tool_message.metrics["model"] == "gpt-4o"
        assert "timing" in tool_message.metrics
        assert tool_message.metrics["timing"]["started_at"] is not None
        assert tool_message.metrics["timing"]["ended_at"] is not None
        assert tool_message.metrics["timing"]["latency"] > 0
        assert tool_message.metrics["weave_call"]["id"] == "test-weave-id"
        assert tool_message.metrics["weave_call"]["ui_url"] == "https://weave.ui/test"

@pytest.mark.asyncio
async def test_go_stream_multiple_messages_metrics():
    """Test metrics tracking across multiple messages in streaming mode"""
    agent = Agent(stream=True, model_name="gpt-4o")
    thread = Thread()
    thread.add_message(Message(role="user", content="Test multiple messages"))
    
    # First response with tool call
    first_chunks = [
        create_streaming_chunk(content="Let me help", tool_calls=[{
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "test_tool",
                "arguments": '{}'
            }
        }])
    ]
    
    # Second response after tool execution
    second_chunks = [
        create_streaming_chunk(content="Here's the result", usage={
            "completion_tokens": 15,
            "prompt_tokens": 25,
            "total_tokens": 40
        })
    ]
    
    mock_weave_call = MagicMock()
    mock_weave_call.id = "test-weave-id"
    mock_weave_call.ui_url = "https://weave.ui/test"
    
    with patch.object(agent, '_get_completion') as mock_get_completion, \
         patch('tyler.models.agent.tool_runner') as mock_tool_runner:
        mock_get_completion.call.side_effect = [
            (async_generator(first_chunks), mock_weave_call),
            (async_generator(second_chunks), mock_weave_call)
        ]
        mock_tool_runner.execute_tool_call = AsyncMock(return_value={
            "name": "test_tool",
            "content": "Tool result"
        })
        
        updates = []
        async for update in agent.go_stream(thread):
            updates.append(update)
        
        # Get all assistant and tool messages
        messages = [
            update.data for update in updates 
            if update.type in (StreamUpdate.Type.ASSISTANT_MESSAGE, StreamUpdate.Type.TOOL_MESSAGE)
        ]
        
        # Verify each message has proper metrics with actual values
        for message in messages:
            assert "metrics" in message.model_dump()
            assert message.metrics["model"] == "gpt-4o"
            assert "timing" in message.metrics
            
            if message.role == "assistant":
                assert "usage" in message.metrics
                if hasattr(message, 'content') and message.content == "Here's the result":
                    # Check specific usage values for the second message
                    assert message.metrics["usage"] == {
                        "completion_tokens": 15,
                        "prompt_tokens": 25,
                        "total_tokens": 40
                    }
                assert "weave_call" in message.metrics
                assert message.metrics["weave_call"]["id"] == "test-weave-id"
                assert message.metrics["weave_call"]["ui_url"] == "https://weave.ui/test"
            
            if message.role == "tool":
                assert message.metrics["timing"]["started_at"] is not None
                assert message.metrics["timing"]["ended_at"] is not None
                assert message.metrics["timing"]["latency"] > 0