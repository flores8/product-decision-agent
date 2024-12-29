from weave import Model
import weave
from litellm import completion
from prompts.Tyler import TylerPrompt
from utils.helpers import get_all_tools
from utils.tool_runner import ToolRunner
import streamlit as st

class TylerModel(Model):
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    prompt: TylerPrompt = TylerPrompt()
    context: str = "You are a pirate"
    tool_runner: ToolRunner = ToolRunner()
    max_tool_recursion: int = 10  # Prevent infinite loops

    def _process_tool_calls(self, response, all_messages: list, all_tools: list, recursion_depth: int = 0) -> str:
        """
        Recursively process tool calls until there are no more or max recursion is reached
        
        Args:
            response: The completion response object
            all_messages: List of conversation messages
            all_tools: List of available tools
            recursion_depth: Current recursion depth
            
        Returns:
            str: The final response content
        """
        if recursion_depth >= self.max_tool_recursion:
            return "Max tool recursion depth reached. Some tools may not have been executed."
            
        if not hasattr(response.choices[0].message, 'tool_calls') or not response.choices[0].message.tool_calls:
            return response.choices[0].message.content
            
        # Add the assistant's message with tool calls to the conversation
        all_messages.append(response.choices[0].message)
        
        # Process each tool call
        for tool_call in response.choices[0].message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = eval(tool_call.function.arguments)
            
            try:
                # Execute the tool
                tool_result = self.tool_runner.run_tool(tool_name, tool_args)
                
                # Add the tool result to the messages
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(tool_result)
                }
                all_messages.append(tool_message)
            except Exception as e:
                # If tool execution fails, add error message
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": f"Error executing tool: {str(e)}"
                }
                all_messages.append(tool_message)
        
        # Make another completion call with the tool results
        next_response = completion(
            model=self.model_name,
            messages=all_messages,
            temperature=self.temperature,
            tools=all_tools
        )
        
        # Recursively process any new tool calls
        return self._process_tool_calls(
            next_response,
            all_messages,
            all_tools,
            recursion_depth + 1
        )

    @weave.op()
    def predict(self, messages: list) -> str:
        """
        Makes a chat completion call using LiteLLM with the Tyler prompt
        
        Args:
            messages (list): List of messages in the conversation
                Each message should be a dict with 'role' and 'content' keys
                
        Returns:
            str: The model's response text
        """
        system_prompt = self.prompt.system_prompt(self.context)
        
        # Load all tools from the tools directory
        all_tools = get_all_tools()
        
        # Combine system prompt with conversation messages
        all_messages = [{"role": "system", "content": system_prompt}] + messages
        
        response = completion(
            model=self.model_name,
            messages=all_messages,
            temperature=self.temperature,
            tools=all_tools
        )
        
        return self._process_tool_calls(response, all_messages, all_tools) 