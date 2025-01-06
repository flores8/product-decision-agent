from typing import List, Optional, Tuple
from weave import Model
import weave
from litellm import completion
from models.thread import Thread, Message
from prompts.AgentPrompt import AgentPrompt
from utils.tool_runner import ToolRunner
from database.thread_store import ThreadStore
import json
from pydantic import Field

class Agent(Model):
    model_name: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.7)
    context: str = Field(default="")
    prompt: AgentPrompt = Field(default_factory=AgentPrompt)
    tools: List[dict] = Field(default_factory=list)
    tool_runner: ToolRunner = Field(default_factory=ToolRunner)
    max_tool_recursion: int = Field(default=10)
    current_recursion_depth: int = Field(default=0)
    thread_store: ThreadStore = Field(default_factory=ThreadStore)

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize tools from tool_runner
        self.tools = []
        for tool_name in self.tool_runner.list_tools():
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": self.tool_runner.get_tool_description(tool_name),
                    "parameters": self.tool_runner.get_tool_parameters(tool_name)
                }
            }
            self.tools.append(tool_def)

    @weave.op()
    def go(self, thread_id: str, new_messages: Optional[List[Message]] = None) -> Tuple[Thread, List[Message]]:
        """
        Process the next step in the thread by generating a response and handling any tool calls.
        
        Args:
            thread_id (str): The ID of the thread to process
            new_messages (List[Message], optional): Messages added during this processing round
            
        Returns:
            Tuple[Thread, List[Message]]: The processed thread and list of new non-user messages
        """
        # Initialize new messages if not provided
        if new_messages is None:
            new_messages = []
            
        thread = self.thread_store.get(thread_id)
        if not thread:
            raise ValueError(f"Thread with ID {thread_id} not found")
            
        # Reset recursion depth on new thread turn
        if self.current_recursion_depth == 0:
            thread.ensure_system_prompt(self.prompt.system_prompt(self.context))
        elif self.current_recursion_depth >= self.max_tool_recursion:
            message = Message(
                role="assistant",
                content="Maximum tool recursion depth reached. Stopping further tool calls."
            )
            thread.add_message(message)
            new_messages.append(message)
            self.thread_store.save(thread)
            return thread, [m for m in new_messages if m.role != "user"]
            
        # Get completion with tools
        response = completion(
            model=self.model_name,
            messages=thread.get_messages_for_chat_completion(),
            temperature=self.temperature,
            tools=self.tools
        )
        
        return self._process_response(response, thread, new_messages)
    
    @weave.op()
    def _process_response(self, response, thread: Thread, new_messages: List[Message]) -> Tuple[Thread, List[Message]]:
        """
        Handle the model response and process any tool calls recursively.
        
        Args:
            response: The completion response object from the language model
            thread (Thread): The thread object to update
            new_messages (List[Message]): Messages added during this processing round
            
        Returns:
            Tuple[Thread, List[Message]]: The processed thread and list of new non-user messages
        """
        message_content = response.choices[0].message.content or ""
        has_tool_calls = hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls
        
        if not has_tool_calls:
            self.current_recursion_depth = 0  # Reset depth when done with tools
            message = Message(
                role="assistant",
                content=message_content
            )
            thread.add_message(message)
            new_messages.append(message)
            self.thread_store.save(thread)
            return thread, [m for m in new_messages if m.role != "user"]
            
        # Add assistant message with tool calls only if there's content
        if message_content.strip():
            message = Message(
                role="assistant",
                content=message_content,
                attributes={"tool_calls": response.choices[0].message.tool_calls}
            )
            thread.add_message(message)
            new_messages.append(message)
        
        # Process tools and add results
        for tool_call in response.choices[0].message.tool_calls:
            result = self._handle_tool_execution(tool_call)
            message = Message(
                role="function",
                content=result["content"],
                name=result["name"],
                attributes={
                    "tool_call_id": result["tool_call_id"],
                    "tool_name": result["name"]
                }
            )
            thread.add_message(message)
            new_messages.append(message)
        
        self.thread_store.save(thread)
        
        # Continue processing with tool results
        self.current_recursion_depth += 1
        return self.go(thread.id, new_messages)

    @weave.op()
    def _handle_tool_execution(self, tool_call) -> dict:
        """
        Execute a single tool call and format the result message
        
        Args:
            tool_call: The tool call object from the model response
            
        Returns:
            dict: Formatted tool result message
        """
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        
        try:
            tool_result = self.tool_runner.run_tool(tool_name, tool_args)
            return {
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": str(tool_result)
            }
        except Exception as e:
            return {
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": f"Error executing tool: {str(e)}"
            } 