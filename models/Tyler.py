from weave import Model
import weave
from litellm import completion
from prompts.Tyler import TylerPrompt
from utils.helpers import get_all_tools
from utils.tool_runner import ToolRunner

class TylerModel(Model):
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    prompt: TylerPrompt = TylerPrompt()
    context: str = ""
    tool_runner: ToolRunner = ToolRunner()
    max_tool_recursion: int = 10  # Prevent infinite loops

    def _process_tool_calls(self, response, messages: list, recursion_depth: int = 0) -> str:
        """
        Recursively process tool calls until there are no more or max recursion is reached
        
        Args:
            response: The completion response object
            messages: List of conversation messages
            recursion_depth: Current recursion depth
            
        Returns:
            str: The final response content
        """
        if recursion_depth >= self.max_tool_recursion:
            return "Max tool recursion depth reached. Some tools may not have been executed."
            
        if not hasattr(response.choices[0].message, 'tool_calls') or not response.choices[0].message.tool_calls:
            return response.choices[0].message.content
            
        # Add the assistant's message with tool calls to the conversation
        messages.append(response.choices[0].message)
        
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
                messages.append(tool_message)
            except Exception as e:
                # If tool execution fails, add error message
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": f"Error executing tool: {str(e)}"
                }
                messages.append(tool_message)
        
        # Recursively call predict with updated messages
        next_response = self.predict(messages)
        return next_response

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
        # Only add system prompt if it's not already there
        if not messages or messages[0].get('role') != 'system':
            system_prompt = self.prompt.system_prompt(self.context)
            messages = [{"role": "system", "content": system_prompt}] + messages
        
        # Load all tools from the tools directory
        all_tools = get_all_tools()
        
        response = completion(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            tools=all_tools
        )
        
        return self._process_tool_calls(response, messages) 