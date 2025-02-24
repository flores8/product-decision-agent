from typing import Optional, List, Tuple, Union, Dict, Any
import weave
from weave import Model, Prompt
from tyler.models.registry import Registry
from tyler.models.thread import Thread, Message
from pydantic import Field, PrivateAttr
from litellm import completion, acompletion
import re
from tyler.utils.logging import get_logger
from datetime import datetime, UTC
from tyler.database.thread_store import ThreadStore
from tyler.utils.tool_runner import tool_runner

# Get configured logger
logger = get_logger(__name__)

class RouterAgentPrompt(Prompt):
    system_template: str = Field(default="""You are a router agent responsible for analyzing incoming messages and directing them to the most appropriate specialized agent. Current date: {current_date}

Your core responsibilities are:
1. Analyzing incoming messages to understand their intent and requirements
2. Identifying if an agent should handle the message
3. Determining which available agent is best suited for the task
4. Creating new conversation threads when needed

Available agents and their purposes:
{agent_descriptions}

When routing messages:
1. First check for explicit @mentions of agents in the message
2. If no explicit mentions, analyze the message content to match with the most appropriate agent's purpose
3. If no agent is clearly suitable, respond with 'none'

Important: You should only respond with the exact name of the most appropriate agent (in lowercase) or 'none' if no agent is needed.
""")

    @weave.op()
    def system_prompt(self, agent_descriptions: str) -> str:
        return self.system_template.format(
            current_date=datetime.now().strftime("%Y-%m-%d %A"),
            agent_descriptions=agent_descriptions
        )

class RouterAgent(Model):
    """Agent responsible for routing messages to appropriate agents"""
    
    registry: Registry = Field(default_factory=Registry)
    model_name: str = Field(default="gpt-4")  # Use GPT-4 for better routing decisions
    prompt: RouterAgentPrompt = Field(default_factory=RouterAgentPrompt)
    thread_store: ThreadStore = Field(default_factory=ThreadStore)
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract @mentions from text"""
        # If text is multimodal, extract the text content
        if isinstance(text, list):
            text = text[0].get("text", "")
        mentions = [m.lower() for m in re.findall(r'@(\w+)', text)]
        if mentions:
            logger.info(f"Found mentions in message: {mentions}")
        return mentions
    
    def _get_agent_selection_completion(self, thread: Thread) -> str:
        """Get completion to select the most appropriate agent"""
        logger.info("Requesting agent selection completion")
        
        # Build agent descriptions including their purposes
        agent_descriptions = []
        for name in self.registry.list_agents():
            agent = self.registry.get_agent(name)
            if agent:
                agent_descriptions.append(f"{name}: {agent.purpose}")
        
        # Log the available agents
        logger.info(f"Available agents for routing: {list(self.registry.list_agents())}")
        
        # Get messages from thread
        messages = [
            {"role": "system", "content": self.prompt.system_prompt("\n".join(agent_descriptions))},
        ]
        
        # Add thread messages
        for msg in thread.messages:
            if msg.role in ["user", "assistant"]:
                content = msg.content
                if isinstance(content, list):
                    content = content[0].get("text", "")
                messages.append({"role": msg.role, "content": content})
        
        # Add final question
        messages.append({"role": "user", "content": "Based on this conversation, which agent should handle the latest message?"})
        
        logger.info(f"Using {len(messages)-2} messages from thread for context")  # -2 for system and final question
        
        response = completion(
            model=self.model_name,
            messages=messages,
            temperature=0.3
        )
        
        selected_agent = response.choices[0].message.content.strip().lower()
        logger.info(f"Agent selection completion returned: {selected_agent}")
        return selected_agent

    @weave.op()
    async def route(self, thread_id: str) -> Optional[str]:
        """
        Route the latest message in a thread to the appropriate agent.
        
        Args:
            thread_id: ID of the thread containing conversation history
            
        Returns:
            Optional[str]: The name of the selected agent, or None if no agent is appropriate
        """
        # Get thread from store
        thread = await self.thread_store.get(thread_id)
        if not thread:
            logger.error(f"Thread with ID {thread_id} not found")
            return None
            
        logger.info(f"Routing message for thread {thread.id}")
        logger.info(f"Thread has {len(thread.messages)} messages")
        
        # Get the latest user message
        latest_message = next((msg for msg in reversed(thread.messages) if msg.role == "user"), None)
        if not latest_message:
            logger.warning("No user message found in thread")
            return None
        
        # First check for explicit mentions
        mentions = self._extract_mentions(latest_message.content)
        for mention in mentions:
            if self.registry.get_agent(mention):
                logger.info(f"Selected agent '{mention}' based on explicit mention")
                return mention
                
        # If no mentions or mentioned agent doesn't exist,
        # use completion to determine best agent
        agent_name = self._get_agent_selection_completion(thread)
        if self.registry.get_agent(agent_name):
            logger.info(f"Selected agent '{agent_name}' based on content analysis")
            return agent_name
        else:
            logger.warning(f"Selected agent '{agent_name}' not found in registry")
            # Log more details about why no agent was selected
            logger.info(f"Latest message content: {latest_message.content}")
            logger.info(f"Available agents: {list(self.registry.list_agents())}")
            return None