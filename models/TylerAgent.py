from typing import List, Optional
from weave import Model
import weave
from litellm import completion
from models.thread import Thread, Message
from prompts.TylerPrompt import TylerPrompt
from utils.tool_runner import ToolRunner
from database.thread_store import ThreadStore
import json
from pydantic import Field

class TylerAgent(Model):
    model_name: str = Field(default="gpt-4o")
    temperature: float = Field(default=0.7)
    context: str = Field(default="")
    prompt: TylerPrompt = Field(default_factory=TylerPrompt)
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
    def go(self, thread_id: str) -> None:
        """
        Process the next step in the thread by generating a response and handling any tool calls.
        
        Args:
            thread_id (str): The ID of the thread to process
            
        Returns:
            None: Updates the thread in the store with new messages
        """
        thread = self.thread_store.get(thread_id)
        if not thread:
            raise ValueError(f"Thread with ID {thread_id} not found")
            
        # Reset recursion depth on new thread turn
        if self.current_recursion_depth == 0:
            thread.ensure_system_prompt(self.prompt.system_prompt(self.context))
        elif self.current_recursion_depth >= self.max_tool_recursion:
            thread.add_message(Message(
                role="assistant",
                content="Maximum tool recursion depth reached. Stopping further tool calls."
            ))
            self.thread_store.save(thread)
            return
            
        # Get completion with tools
        response = completion(
            model=self.model_name,
            messages=thread.get_messages_for_chat_completion(),
            temperature=self.temperature,
            tools=self.tools
        )
        
        self._process_response(response, thread)
    
    @weave.op()
    def _process_response(self, response, thread: Thread) -> None:
        """
        Handle the model response and process any tool calls recursively.
        
        Args:
            response: The completion response object from the language model
            thread (Thread): The thread object to update
            
        Returns:
            None: Updates the thread in the store with new messages
        """
        message_content = response.choices[0].message.content or ""
        has_tool_calls = hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls
        
        if not has_tool_calls:
            self.current_recursion_depth = 0  # Reset depth when done with tools
            thread.add_message(Message(
                role="assistant",
                content=message_content
            ))
            self.thread_store.save(thread)
            return
            
        # Add assistant message with tool calls only if there's content
        if message_content.strip():
            thread.add_message(Message(
                role="assistant",
                content=message_content,
                attributes={"tool_calls": response.choices[0].message.tool_calls}
            ))
        
        # Process tools and add results
        for tool_call in response.choices[0].message.tool_calls:
            result = self._handle_tool_execution(tool_call)
            thread.add_message(Message(
                role="function",
                content=result["content"],
                name=result["name"],
                attributes={
                    "tool_call_id": result["tool_call_id"],
                    "tool_name": result["name"]
                }
            ))
        
        self.thread_store.save(thread)
        
        # Continue processing with tool results
        self.current_recursion_depth += 1
        self.go(thread.id)

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