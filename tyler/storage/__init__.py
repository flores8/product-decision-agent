"""File storage module for Tyler"""
import os
from typing import Optional, Set
from .file_store import FileStore

class FileStoreManager:
    """Manages file store instance and configuration"""
    _instance: Optional[FileStore] = None
    
    @classmethod
    def get_instance(cls) -> FileStore:
        """Get the initialized file store instance
        
        Returns:
            The initialized FileStore
            
        Raises:
            RuntimeError: If file store hasn't been initialized
        """
        if cls._instance is None:
            # Auto-initialize with defaults
            cls._instance = FileStore()
        return cls._instance
    
    @classmethod
    def set_instance(cls, store: FileStore) -> None:
        """Set the file store instance"""
        cls._instance = store

# Convenience function for backwards compatibility
def get_file_store() -> FileStore:
    """Get the initialized file store instance"""
    return FileStoreManager.get_instance() 