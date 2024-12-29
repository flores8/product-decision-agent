from weave import Model
import weave
from litellm import completion
from prompts.Tyler import TylerPrompt
from utils.helpers import get_all_tools

class TylerModel(Model):
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    prompt: TylerPrompt = TylerPrompt()
    context: str = "You are a pirate"

    @weave.op()
    def predict(self, user_message: str) -> str:
        """
        Makes a chat completion call using LiteLLM with the Tyler prompt
        
        Args:
            user_message (str): The user's input message
            
        Returns:
            str: The model's response text
        """
        system_prompt = self.prompt.system_prompt(self.context)
        
        # Load all tools from the tools directory
        all_tools = get_all_tools()
        
        response = completion(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=self.temperature,
            tools=all_tools
        )
        
        return response.choices[0].message.content 