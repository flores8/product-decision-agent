from typing import Optional, List
from models.Agent import Agent
from models.Registry import Registry
from models.thread import Thread, Message
from pydantic import Field
from litellm import completion
import weave
import re
import uuid

class RouterAgent(Agent):
    """Agent responsible for routing messages to appropriate agents"""
    
    registry: Registry = Field(default_factory=Registry)
    model_name: str = Field(default="gpt-4")  # Use GPT-4 for better routing decisions
    
    def __init__(self, **data):
        super().__init__(**data)
        self.context = """You are a router agent responsible for:
1. Analyzing incoming messages
2. Identifying if an agent should handle the message
3. Determining which agent is best suited for the task
4. Creating new threads when needed
"""
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract @mentions from text"""
        return [m.lower() for m in re.findall(r'@(\w+)', text)]
    
    def _should_assign_agent(self, message: Message) -> bool:
        """Determine if message requires agent involvement"""
        # For now, assume all messages need agent involvement
        # In the future, this could be more sophisticated
        return True
    
    @weave.op()
    def _get_agent_selection_completion(self, message_content: str) -> str:
        """Get completion to select the most appropriate agent"""
        response = completion(
            model=self.model_name,
            messages=[
                {"role": "system", "content": f"""You are a router that determines which agent should handle a request.
Available agents: {', '.join(self.registry.list_agents())}

Respond ONLY with the name of the most appropriate agent, or 'none' if no agent is needed."""},
                {"role": "user", "content": message_content}
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip().lower()
    
    def _select_agent(self, message: Message) -> Optional[str]:
        """Select the most appropriate agent for the message"""
        # First check for explicit mentions
        mentions = self._extract_mentions(message.content)
        for mention in mentions:
            if self.registry.has_agent(mention):
                return mention
                
        # If no mentions or mentioned agent doesn't exist,
        # use completion to determine best agent
        agent_name = self._get_agent_selection_completion(message.content)
        return agent_name if self.registry.has_agent(agent_name) else None
    
    @weave.op()
    def route(self, thread_id: str) -> None:
        """Process thread and route to appropriate agent if needed"""
        thread = self.thread_store.get(thread_id)
        if not thread:
            raise ValueError(f"Thread with ID {thread_id} not found")
            
        # Get the last user message
        last_message = thread.get_last_message_by_role("user")
        if not last_message:
            return
            
        # Check if we should assign an agent
        if not self._should_assign_agent(last_message):
            thread.add_message(Message(
                role="assistant",
                content="I don't think this requires agent assistance."
            ))
            self.thread_store.save(thread)
            return
            
        # Select appropriate agent
        agent_name = self._select_agent(last_message)
        if not agent_name:
            thread.add_message(Message(
                role="assistant",
                content="I couldn't determine which agent should handle this request."
            ))
            self.thread_store.save(thread)
            return
            
        # Get the agent and process the thread
        agent = self.registry.get_agent(agent_name)
        if agent:
            # Update thread attributes with assigned agent
            thread.attributes["assigned_agent"] = agent_name
            self.thread_store.save(thread)
            
            # Let the agent process the thread
            agent.go(thread_id)
            
    def route_new_message(self, message: str) -> Optional[str]:
        """Create a new thread if message needs agent assignment and route it.
        Returns thread_id if created and routed, None if no agent needed."""
        
        # Check if we should assign an agent
        temp_message = Message(role="user", content=message)
        if not self._should_assign_agent(temp_message):
            return None
            
        # Create new thread
        thread_id = f"api-{str(uuid.uuid4())}"
        thread = Thread(
            id=thread_id,
            title=f"{message[:30]}..." if len(message) > 30 else message,
            attributes={"source": "api"}
        )
        
        # Add the message
        thread.add_message(temp_message)
        self.thread_store.save(thread)
        
        # Route the thread
        self.route(thread_id)
        return thread_id 