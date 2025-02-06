from typing import List, Optional, Tuple, Union, Dict
from weave import Model, Prompt
import weave
from litellm import completion
from tyler.models.thread import Thread, Message
from tyler.utils.tool_runner import tool_runner
from tyler.database.memory_store import MemoryThreadStore
from pydantic import Field, PrivateAttr
from datetime import datetime, UTC
from tyler.tools.file_processor import FileProcessor
import magic
import base64
import os

class AgentPrompt(Prompt):
    system_template: str = Field(default="""You are {name}, an LLM agent with a specific purpose that can converse with users, answer questions, and when necessary, use tools to perform tasks.
Current date: {current_date}
                                 
Your purpose is: {purpose}

Some are some relevant notes to help you accomplish your purpose:
```
{notes}
```

Based on the user's input, follow this routine:
1. If the user makes a statement or shares information, respond appropriately with acknowledgment.
2. If the user's request is vague, incomplete, or missing information needed to complete the task, use the relevant context to understand the user's request. If you don't find an answer in the context, ask probing questions to understand the user's request deeper. You can ask a maximum of 5 probing questions.
3. If you can answer the user's request using the relevant context or your knowledge (you are a powerful AI model with a large knowledge base), then provide a clear and concise answer.  
4. If the request requires gathering information or performing actions beyond your chat completion capabilities use the tools provided to you. After the tool is executed, you will automatically receive the results and can then formulate the next step to take.
                                 
Important: Always include a sentence explaining how you arrived at your answer in your response.  Take your time to think about the answer and include a sentence explaining your thought process.
""")

    @weave.op()
    def system_prompt(self, purpose: str, name: str, notes: str = "") -> str:
        return self.system_template.format(
            current_date=datetime.now().strftime("%Y-%m-%d %A"),
            purpose=purpose,
            name=name,
            notes=notes
        )

class Agent(Model):
    model_name: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.7)
    name: str = Field(default="Tyler")
    purpose: str = Field(default="To be a helpful assistant.")
    notes: str = Field(default="")
    tools: List[Union[str, Dict]] = Field(default_factory=list, description="List of tools available to the agent. Can include built-in tool module names (as strings) and custom tools (as dicts with 'definition' and 'implementation' keys).")
    max_tool_recursion: int = Field(default=10)
    thread_store: Optional[object] = Field(default_factory=MemoryThreadStore, description="Thread storage implementation. Uses in-memory storage by default.")
    
    _prompt: AgentPrompt = PrivateAttr(default_factory=AgentPrompt)
    _current_recursion_depth: int = PrivateAttr(default=0)
    _file_processor: FileProcessor = PrivateAttr(default_factory=FileProcessor)

    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "allow"
    }

    def __init__(self, **data):
        super().__init__(**data)
        
        # Process tools parameter to handle both module names and custom tools
        processed_tools = []
        
        for tool in self.tools:
            if isinstance(tool, str):
                # If tool is a string, treat it as a module name
                module_tools = tool_runner.load_tool_module(tool)
                processed_tools.extend(module_tools)
            elif isinstance(tool, dict):
                # If tool is a dict, it should have both definition and implementation
                if 'definition' not in tool or 'implementation' not in tool:
                    raise ValueError(
                        "Custom tools must be dictionaries with 'definition' and 'implementation' keys. "
                        "The 'definition' should be the OpenAI function definition, and "
                        "'implementation' should be the callable that implements the tool."
                    )
                # Register the implementation with the tool runner
                tool_name = tool['definition']['function']['name']
                tool_runner.register_tool(tool_name, tool['implementation'])
                # Add only the definition to processed tools
                processed_tools.append(tool['definition'])
                
        self.tools = processed_tools

    def _process_message_files(self, message: Message) -> None:
        """Process any files attached to the message"""
        for attachment in message.attachments:
            try:
                # Get content as bytes
                content = attachment.get_content_bytes()
                
                # Check if it's an image
                mime_type = magic.from_buffer(content, mime=True)
                if mime_type.startswith('image/'):
                    # Store the image content for direct use in completion
                    attachment.processed_content = {
                        "type": "image",
                        "content": base64.b64encode(content).decode('utf-8'),
                        "mime_type": mime_type
                    }
                else:
                    # Use file processor for PDFs and other supported types
                    result = self._file_processor.process_file(content, attachment.filename)
                    attachment.processed_content = result
                    
                # Store the detected mime type if not already set
                if not attachment.mime_type:
                    attachment.mime_type = mime_type
                    
            except Exception as e:
                attachment.processed_content = {"error": f"Failed to process file: {str(e)}"}
        
        # After processing all attachments, update the message content if there are images
        image_attachments = [
            att for att in message.attachments 
            if att.processed_content and att.processed_content.get("type") == "image"
        ]
        
        if image_attachments:
            # Only convert to multimodal format if we haven't already
            if not isinstance(message.content, list):
                # Create a multimodal message with proper typing
                message_content = [
                    {
                        "type": "text",
                        "text": message.content if isinstance(message.content, str) else ""
                    }
                ]
                
                # Add each image with proper typing
                for attachment in image_attachments:
                    message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{attachment.mime_type};base64,{attachment.processed_content['content']}"
                        }
                    })
                
                message.content = message_content

    @weave.op()
    async def go(self, thread_or_id: Union[str, Thread], new_messages: Optional[List[Message]] = None) -> Tuple[Thread, List[Message]]:
        """
        Process the next step in the thread by generating a response and handling any tool calls.
        
        Args:
            thread_or_id (Union[str, Thread]): Either a Thread object or thread ID to process
            new_messages (List[Message], optional): Messages added during this processing round
            
        Returns:
            Tuple[Thread, List[Message]]: The processed thread and list of new non-user messages
        """
        # Initialize new messages if not provided
        if new_messages is None:
            new_messages = []
            
        # Get the thread object
        if isinstance(thread_or_id, str):
            if not self.thread_store:
                raise ValueError("Thread store is required when passing thread ID")
            thread = await self.thread_store.get(thread_or_id)
            if not thread:
                raise ValueError(f"Thread with ID {thread_or_id} not found")
        else:
            thread = thread_or_id
            
        # Reset recursion depth on new thread turn
        if self._current_recursion_depth == 0:
            system_prompt = self._prompt.system_prompt(self.purpose, self.name, self.notes)
            thread.ensure_system_prompt(system_prompt)
            
            # Process any files in the last user message
            last_message = thread.get_last_message_by_role("user")
            if last_message and last_message.attachments:
                self._process_message_files(last_message)
                # Save the thread if we have a thread store
                if self.thread_store:
                    await self.thread_store.save(thread)
                
        elif self._current_recursion_depth >= self.max_tool_recursion:
            message = Message(
                role="assistant",
                content="Maximum tool recursion depth reached. Stopping further tool calls."
            )
            thread.add_message(message)
            new_messages.append(message)
            if self.thread_store:
                await self.thread_store.save(thread)
            return thread, [m for m in new_messages if m.role != "user"]
            
        # Get completion with tools
        completion_params = {
            "model": self.model_name,
            "messages": thread.get_messages_for_chat_completion(),
            "temperature": self.temperature,
        }
        
        if len(self.tools) > 0:
            completion_params["tools"] = self.tools
        
        # Track only API call time - the most important metric
        api_start_time = datetime.now(UTC)
        response = completion(**completion_params)
        
        # Create metrics dict with only essential data
        metrics = {
            "completion_tokens": response.usage.completion_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "total_tokens": response.usage.total_tokens,
            "model": self.model_name,
            "latency": (datetime.now(UTC) - api_start_time).total_seconds() * 1000
        }
        
        return await self._process_response(response, thread, new_messages, metrics)
    
    @weave.op()
    async def _process_response(self, response, thread: Thread, new_messages: List[Message], metrics: Dict) -> Tuple[Thread, List[Message]]:
        assistant_message = response.choices[0].message
        message_content = assistant_message.content
        tool_calls = getattr(assistant_message, 'tool_calls', None)
        has_tool_calls = tool_calls is not None and len(tool_calls) > 0
        
        # Serialize tool calls if present
        serialized_tool_calls = None
        if has_tool_calls:
            serialized_tool_calls = []
            for call in tool_calls:
                call_dict = {
                    "id": call.id,
                    "type": getattr(call, 'type', 'function'),
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments
                    }
                }
                serialized_tool_calls.append(call_dict)
        
        # Create message with only API metrics
        message = Message(
            role="assistant",
            content=message_content,
            tool_calls=serialized_tool_calls,
            metrics=metrics
        )
        thread.add_message(message)
        new_messages.append(message)
        
        if not has_tool_calls:
            self._current_recursion_depth = 0
            if self.thread_store:
                await self.thread_store.save(thread)
            return thread, [m for m in new_messages if m.role != "user"]
        
        # Process tools and add results - no metrics for tool calls to minimize overhead
        for tool_call in tool_calls:
            result = await self._handle_tool_execution(tool_call)
            message = Message(
                role="tool",
                content=result["content"],
                name=result["name"],
                tool_call_id=tool_call.id
            )
            thread.add_message(message)
            new_messages.append(message)
        
        if self.thread_store:
            await self.thread_store.save(thread)
        self._current_recursion_depth += 1
        return await self.go(thread, new_messages)

    @weave.op()
    async def _handle_tool_execution(self, tool_call) -> dict:
        """
        Execute a single tool call and format the result message
        
        Args:
            tool_call: The tool call object from the model response
            
        Returns:
            dict: Formatted tool result message
        """
        return await tool_runner.execute_tool_call(tool_call) 