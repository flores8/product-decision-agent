from typing import List, Dict, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from .message import Message

class Conversation(BaseModel):
    """Represents a conversation containing multiple messages"""
    id: str
    title: str
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict)
    
    def ensure_system_prompt(self, prompt: str) -> None:
        """Ensures system prompt is first message, adding or updating if needed"""
        if not self.messages or self.messages[0].role != "system":
            self.messages.insert(0, Message(role="system", content=prompt))
        elif self.messages[0].content != prompt:
            self.messages[0].content = prompt

    def add_message(self, message: Message) -> None:
        """Add a new message to the conversation"""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def get_messages_for_chat_completion(self) -> List[Dict]:
        """Return messages in the format expected by chat completion APIs"""
        api_messages = []
        for msg in self.messages:
            message_dict = {
                "role": msg.role,
                "content": msg.content
            }
            
            # Only include name if it exists and role is 'function'
            if msg.name and msg.role == "function":
                message_dict["name"] = msg.name
                
            # Only include function_call if it exists
            if msg.function_call:
                message_dict["function_call"] = msg.function_call
                
            api_messages.append(message_dict)
        
        return api_messages

    def clear_messages(self) -> None:
        """Clear all messages from the conversation"""
        self.messages = []
        self.updated_at = datetime.utcnow()