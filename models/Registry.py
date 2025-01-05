from typing import Dict, List, Type, Optional
from pydantic import BaseModel, Field
from models.Agent import Agent

class Registry(BaseModel):
    """Registry for managing available agents in the system"""
    
    agents: Dict[str, Type[Agent]] = Field(default_factory=dict)
    agent_instances: Dict[str, Agent] = Field(default_factory=dict)
    
    def register_agent(self, name: str, agent_class: Type[Agent]) -> None:
        """Register a new agent class"""
        self.agents[name.lower()] = agent_class
        
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get or create an agent instance by name"""
        name = name.lower()
        if name not in self.agents:
            return None
            
        if name not in self.agent_instances:
            self.agent_instances[name] = self.agents[name]()
            
        return self.agent_instances[name]
        
    def list_agents(self) -> List[str]:
        """List all registered agent names"""
        return list(self.agents.keys())
        
    def has_agent(self, name: str) -> bool:
        """Check if an agent exists by name"""
        return name.lower() in self.agents 