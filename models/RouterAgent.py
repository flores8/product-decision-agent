from typing import Optional, List, Dict, Any, Tuple
from models.Agent import Agent
from models.Registry import Registry
from models.Thread import Thread, Message
from pydantic import Field
from litellm import completion
import weave
import re
import uuid
import logging

logger = logging.getLogger(__name__)

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
        mentions = [m.lower() for m in re.findall(r'@(\w+)', text)]
        if mentions:
            logger.info(f"Found mentions in message: {mentions}")
        return mentions
    
    def _should_assign_agent(self, message: Message) -> bool:
        """Determine if message requires agent involvement"""
        # For now, assume all messages need agent involvement
        return True
    
    @weave.op()
    def _get_agent_selection_completion(self, message_content: str) -> str:
        """Get completion to select the most appropriate agent"""
        logger.info("Requesting agent selection completion")
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
        
        selected_agent = response.choices[0].message.content.strip().lower()
        logger.info(f"Agent selection completion returned: {selected_agent}")
        return selected_agent
    
    def _select_agent(self, message: Message) -> Optional[str]:
        """Select the most appropriate agent for the message"""
        logger.info("Selecting agent for message")
        
        # First check for explicit mentions
        mentions = self._extract_mentions(message.content)
        for mention in mentions:
            if self.registry.has_agent(mention):
                logger.info(f"Selected agent '{mention}' based on explicit mention")
                return mention
                
        # If no mentions or mentioned agent doesn't exist,
        # use completion to determine best agent
        agent_name = self._get_agent_selection_completion(message.content)
        if self.registry.has_agent(agent_name):
            logger.info(f"Selected agent '{agent_name}' based on content analysis")
            return agent_name
        else:
            logger.warning(f"Selected agent '{agent_name}' not found in registry")
            return None
    
    def _process_with_agent(self, agent_name: str, thread: Thread) -> Tuple[Thread, List[Message]]:
        """Process a thread with the specified agent."""
        logger.info(f"Processing thread {thread.id} with agent '{agent_name}'")
        
        agent = self.registry.get_agent(agent_name)
        if agent:
            # Update thread attributes with assigned agent
            thread.attributes["assigned_agent"] = agent_name
            self.thread_store.save(thread)
            
            # Let the agent process the thread and wait for result
            logger.info(f"Starting agent processing for thread {thread.id}")
            result = agent.go(thread.id)
            logger.info(f"Agent processing complete for thread {thread.id}")
            return result
        else:
            # Handle case where agent doesn't exist
            logger.error(f"Agent '{agent_name}' not found in registry")
            message = Message(
                role="assistant",
                content=f"Agent '{agent_name}' was selected but could not be found."
            )
            thread.add_message(message)
            self.thread_store.save(thread)
            return thread, [message]

    @weave.op()
    def route(self, message: str, source: Dict[str, str]) -> Tuple[Thread, List[Message]]:
        """Process message and route to appropriate agent if needed"""
        logger.info(f"Routing message from source {source['name']}")
        
        # Search for existing thread by source
        existing_threads = self.thread_store.find_by_source(source["name"], {"thread_id": source["thread_id"]})
        
        if existing_threads:
            thread = existing_threads[0]
            logger.info(f"Found existing thread {thread.id}")
        else:
            # Create new thread if none exists
            thread = Thread(
                title=f"{message[:30]}..." if len(message) > 30 else message,
                source=source
            )
            logger.info(f"Created new thread {thread.id}")
        
        # Add the message
        thread.add_message(Message(role="user", content=message))
        self.thread_store.save(thread)
            
        # Select appropriate agent
        agent_name = self._select_agent(Message(role="user", content=message))

        if not agent_name:
            logger.warning("No suitable agent found for message")
            message = Message(
                role="assistant",
                content="I couldn't determine which agent should handle this request."
            )
            thread.add_message(message)
            self.thread_store.save(thread)
            return thread, [message]
            
        # Process with selected agent and wait for result
        return self._process_with_agent(agent_name, thread)