from typing import List, Optional
from weave import Model
import weave
from litellm import completion
from models.conversation import Conversation, Message
from prompts.TylerPrompt import TylerPrompt
from utils.tool_runner import ToolRunner
from database.conversation_store import ConversationStore
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
    conversation_store: ConversationStore = Field(default_factory=ConversationStore)

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
    def go(self, conversation_id: str) -> None:
        """
        Process the next step in the conversation by generating a response and handling any tool calls.
        
        Args:
            conversation_id (str): The ID of the conversation to process
            
        Returns:
            None: Updates the conversation in the store with new messages
        """
        conversation = self.conversation_store.get(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")
            
        # Reset recursion depth on new conversation turn
        if self.current_recursion_depth == 0:
            conversation.ensure_system_prompt(self.prompt.system_prompt(self.context))
        elif self.current_recursion_depth >= self.max_tool_recursion:
            conversation.add_message(Message(
                role="assistant",
                content="Maximum tool recursion depth reached. Stopping further tool calls."
            ))
            self.conversation_store.save(conversation)
            return
            
        # Get completion with tools
        response = completion(
            model=self.model_name,
            messages=conversation.get_messages_for_chat_completion(),
            temperature=self.temperature,
            tools=self.tools
        )
        
        self._process_response(response, conversation)
    
    @weave.op()
    def _process_response(self, response, conversation: Conversation) -> None:
        """
        Handle the model response and process any tool calls recursively.
        
        Args:
            response: The completion response object from the language model
            conversation (Conversation): The conversation object to update
            
        Returns:
            None: Updates the conversation in the store with new messages
        """
        message_content = response.choices[0].message.content or ""
        has_tool_calls = hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls
        
        if not has_tool_calls:
            self.current_recursion_depth = 0  # Reset depth when done with tools
            conversation.add_message(Message(
                role="assistant",
                content=message_content
            ))
            self.conversation_store.save(conversation)
            return
            
        # Add assistant message with tool calls only if there's content
        if message_content.strip():
            conversation.add_message(Message(
                role="assistant",
                content=message_content,
                attributes={"tool_calls": response.choices[0].message.tool_calls}
            ))
        
        # Process tools and add results
        for tool_call in response.choices[0].message.tool_calls:
            result = self._handle_tool_execution(tool_call)
            conversation.add_message(Message(
                role="function",
                content=result["content"],
                name=result["name"],
                attributes={
                    "tool_call_id": result["tool_call_id"],
                    "tool_name": result["name"]
                }
            ))
        
        self.conversation_store.save(conversation)
        
        # Continue processing with tool results
        self.current_recursion_depth += 1
        self.go(conversation.id)

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