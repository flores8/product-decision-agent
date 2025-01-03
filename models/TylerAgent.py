from typing import List, Optional
from weave import Model
import weave
from litellm import completion
from models.conversation import Conversation, Message
from prompts.TylerPrompt import TylerPrompt
from utils.tool_runner import ToolRunner
from database.conversation_store import ConversationStore
import json

class TylerAgent(Model):
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    context: str = ""
    prompt: TylerPrompt = TylerPrompt()
    tools: List[dict] = []
    tool_runner: ToolRunner = ToolRunner()
    max_tool_recursion: int = 10
    _current_recursion_depth: int = 0
    conversation_store: ConversationStore = ConversationStore()

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
        if self._current_recursion_depth == 0:
            conversation.ensure_system_prompt(self.prompt.system_prompt(self.context))
        elif self._current_recursion_depth >= self.max_tool_recursion:
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
            self._current_recursion_depth = 0  # Reset depth when done with tools
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
        self._current_recursion_depth += 1
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
        """Execute a single tool call and format the result message"""
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