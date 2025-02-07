from typing import List, Optional, Dict, Any
from tyler.models.thread import Thread
from tyler.models.message import Message

class MemoryThreadStore:
    """
    A simple in-memory thread store implementation using a Python dictionary.
    
    Key characteristics:
    - Fastest possible performance (direct dictionary access)
    - No persistence (data is lost when program exits)
    - No setup required (works out of the box)
    - Perfect for scripts and one-off conversations
    - Great for testing and development
    
    Usage:
        # Used by default when creating an agent
        agent = Agent(purpose="My purpose")  # Uses MemoryThreadStore
        
        # Or explicitly create and use
        store = MemoryThreadStore()
        agent = Agent(purpose="My purpose", thread_store=store)
        
        # Thread operations are immediate, no need to save
        thread = Thread()
        store.save_thread(thread)  # Optional with memory store
        
        # Can pass either thread or thread.id to agent
        result = await agent.go(thread)  # or thread.id
    """
    
    def __init__(self):
        """Initialize an empty thread store."""
        self._threads: Dict[str, Thread] = {}
    
    def save(self, thread: Thread) -> Thread:
        """Save a thread to memory."""
        self._threads[thread.id] = thread
        return thread
    
    def get(self, thread_id: str) -> Optional[Thread]:
        """Get a thread by ID."""
        return self._threads.get(thread_id)
    
    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread by ID."""
        if thread_id in self._threads:
            del self._threads[thread_id]
            return True
        return False
    
    def list_threads(self, limit: int = 100, offset: int = 0) -> List[Thread]:
        """List threads with pagination."""
        threads = sorted(
            self._threads.values(),
            key=lambda t: t.updated_at if hasattr(t, 'updated_at') else t.created_at,
            reverse=True
        )
        return threads[offset:offset + limit]
    
    def find_by_attributes(self, attributes: Dict[str, Any]) -> List[Thread]:
        """Find threads by matching attributes."""
        matching_threads = []
        for thread in self._threads.values():
            if all(
                thread.attributes.get(k) == v 
                for k, v in attributes.items()
            ):
                matching_threads.append(thread)
        return matching_threads
    
    def find_by_source(self, source_name: str, properties: Dict[str, Any]) -> List[Thread]:
        """Find threads by source name and properties."""
        matching_threads = []
        for thread in self._threads.values():
            source = getattr(thread, 'source', {})
            if (
                isinstance(source, dict) and 
                source.get('name') == source_name and
                all(source.get(k) == v for k, v in properties.items())
            ):
                matching_threads.append(thread)
        return matching_threads
    
    def list_recent(self, limit: int = 30) -> List[Thread]:
        """List recent threads ordered by updated_at timestamp."""
        return self.list_threads(limit=limit)
    
    def add_message(self, thread_id: str, message: Message) -> None:
        """Add a message to a thread."""
        if thread := self._threads.get(thread_id):
            thread.add_message(message)
    
    def get_messages(self, thread_id: str) -> List[Message]:
        """Get all messages for a thread."""
        if thread := self._threads.get(thread_id):
            return thread.messages
        return [] 