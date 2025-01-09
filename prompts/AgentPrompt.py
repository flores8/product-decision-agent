class AgentPrompt:
    def __init__(self):
        self.system_prompt = ""
        self.user_prompt = ""
        
    def get_system_prompt(self) -> str:
        return self.system_prompt
        
    def get_user_prompt(self) -> str:
        return self.user_prompt
        
    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt
        
    def set_user_prompt(self, prompt: str) -> None:
        self.user_prompt = prompt 