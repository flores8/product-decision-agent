from typing import Optional, List, Dict, Any, Tuple
from models.Agent import Agent
from models.Registry import Registry
from models.Thread import Thread, Message
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
    
    def _process_with_agent(self, agent_name: str, thread: Thread) -> Tuple[Thread, List[Message]]:
        """Process a thread with the specified agent.
        
        Args:
            agent_name: Name of the agent to process the thread
            thread: Thread object to be processed
            
        Returns:
            Tuple[Thread, List[Message]]: The processed thread and new assistant messages
        """
        agent = self.registry.get_agent(agent_name)
        if agent:
            # Update thread attributes with assigned agent
            thread.attributes["assigned_agent"] = agent_name
            self.thread_store.save(thread)
            
            # Let the agent process the thread and wait for result
            return agent.go(thread.id)
        else:
            # Handle case where agent doesn't exist
            message = Message(
                role="assistant",
                content=f"Agent '{agent_name}' was selected but could not be found."
            )
            thread.add_message(message)
            self.thread_store.save(thread)
            return thread, [message]

    @weave.op()
    def route(self, message: str, source: Dict[str, str]) -> Tuple[Thread, List[Message]]:
        """Process message and route to appropriate agent if needed
        
        Args:
            message: The message content
            source: Source information containing name and thread_id
            
        Returns:
            Tuple[Thread, List[Message]]: The processed thread and new assistant messages
        """
        # Search for existing thread by source
        existing_threads = self.thread_store.find_by_source(source["name"], {"thread_id": source["thread_id"]})
        
        if existing_threads:
            thread = existing_threads[0]
        else:
            # Create new thread if none exists
            thread = Thread(
                title=f"{message[:30]}..." if len(message) > 30 else message,
                source=source
            )
        
        # Add the message
        thread.add_message(Message(role="user", content=message))
        self.thread_store.save(thread)
            
        # Select appropriate agent
        agent_name = self._select_agent(Message(role="user", content=message))

        if not agent_name:
            message = Message(
                role="assistant",
                content="I couldn't determine which agent should handle this request."
            )
            thread.add_message(message)
            self.thread_store.save(thread)
            return thread, [message]
            
        # Process with selected agent and wait for result
        return self._process_with_agent(agent_name, thread)