from weave import Model
import weave
from litellm import completion
from prompts.TylerPrompt import TylerPrompt
from utils.helpers import get_all_tools
from utils.tool_runner import ToolRunner
import json

class TylerModel(Model):
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    prompt: TylerPrompt = TylerPrompt()
    context: str = ""
    tool_runner: ToolRunner = ToolRunner()
    max_tool_recursion: int = 10

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
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": str(tool_result)
            }
        except Exception as e:
            return {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": f"Error executing tool: {str(e)}"
            }

    @weave.op()
    def _process_response(self, response, messages: list, recursion_depth: int = 0) -> str:
        """
        Process the model's response, handling any tool calls
        
        Args:
            response: The completion response object
            messages: List of conversation messages
            recursion_depth: Current recursion depth
            
        Returns:
            str: Final response content
        """
        if recursion_depth >= self.max_tool_recursion:
            return "Max tool recursion depth reached. Some tools may not have been executed."
            
        # If no tool calls, return the content directly
        if not hasattr(response.choices[0].message, 'tool_calls') or not response.choices[0].message.tool_calls:
            return response.choices[0].message.content
            
        # Add the assistant's message with tool calls
        messages.append(response.choices[0].message)
        
        # Process all tool calls and add results to messages
        for tool_call in response.choices[0].message.tool_calls:
            tool_result = self._handle_tool_execution(tool_call)
            messages.append(tool_result)
        
        # Get next response with tool results
        next_response = self.predict(messages)
        return next_response

    @weave.op()
    def predict(self, messages: list) -> str:
        """
        Makes a chat completion call and processes the response
        
        Args:
            messages (list): List of conversation messages
                
        Returns:
            str: The model's final response text
        """
        # Add system prompt if needed
        if not messages or messages[0].get('role') != 'system':
            system_prompt = self.prompt.system_prompt(self.context)
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        # Get completion with tools
        response = completion(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            tools=get_all_tools()
        )
        
        return self._process_response(response, messages) 