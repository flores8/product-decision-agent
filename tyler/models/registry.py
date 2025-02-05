from typing import Dict, List, Type, Optional, Union
from pydantic import BaseModel, Field
from tyler.models.agent import Agent

class Registry(BaseModel):
    """Registry for managing available agents in the system"""
    
    agents: Dict[str, Union[Type[Agent], Agent]] = Field(default_factory=dict)
    agent_instances: Dict[str, Agent] = Field(default_factory=dict)
    
    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "allow"
    }
    
    def register_agent(self, name: str, agent: Union[Type[Agent], Agent], **kwargs) -> None:
        """Register a new agent class or instance
        
        Args:
            name: Name to register the agent under
            agent: Either an Agent class or a pre-configured Agent instance
            **kwargs: Optional configuration parameters when registering an Agent class
        """
        name = name.lower()
        if isinstance(agent, Agent):
            self.agents[name] = agent
            self.agent_instances[name] = agent
        else:
            self.agents[name] = agent
            if kwargs:
                self.agent_instances[name] = agent(**kwargs)
        
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get or create an agent instance by name"""
        name = name.lower()
        if name not in self.agents:
            return None
            
        if name not in self.agent_instances:
            agent = self.agents[name]
            if isinstance(agent, type):  # If it's a class
                self.agent_instances[name] = agent()
            else:  # If it's an instance
                self.agent_instances[name] = agent
            
        return self.agent_instances[name]
        
    def list_agents(self) -> List[str]:
        """List all registered agent names"""
        return list(self.agents.keys())
        
    def has_agent(self, name: str) -> bool:
        """Check if an agent exists by name"""
        return name.lower() in self.agents 