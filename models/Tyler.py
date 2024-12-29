from weave import Model
import weave
from litellm import completion
from prompts.Tyler import TylerPrompt
from utils.helpers import get_all_tools
import streamlit as st

class TylerModel(Model):
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    prompt: TylerPrompt = TylerPrompt()
    context: str = "You are a pirate"

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
        
        return response.choices[0].message.content 