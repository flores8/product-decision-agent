from typing import Dict, Optional, Any, Union
from pydantic import BaseModel
from base64 import b64encode
import base64

class Attachment(BaseModel):
    """Represents a file attached to a message"""
    filename: str
    content: Optional[Union[bytes, str]] = None  # Can be either bytes or base64 string
    mime_type: Optional[str] = None
    processed_content: Optional[Dict[str, Any]] = None
    file_id: Optional[str] = None  # Reference to stored file
    storage_path: Optional[str] = None  # Path in storage backend
    storage_backend: Optional[str] = None  # Storage backend type

    def model_dump(self) -> Dict[str, Any]:
        """Convert attachment to a dictionary suitable for JSON serialization"""
        data = {
            "filename": self.filename,
            "mime_type": self.mime_type,
            "processed_content": self.processed_content,
            "file_id": self.file_id,
            "storage_path": self.storage_path,
            "storage_backend": self.storage_backend
        }
        
        # Only include content if no file_id (backwards compatibility)
        if not self.file_id and self.content is not None:
            # Convert bytes to base64 string for JSON serialization
            if isinstance(self.content, bytes):
                data["content"] = b64encode(self.content).decode('utf-8')
            else:
                data["content"] = self.content
                
        return data
        
    async def get_content_bytes(self) -> bytes:
        """Get the content as bytes, converting from base64 if necessary
        
        If file_id is present, retrieves content from file storage.
        Otherwise falls back to content field.
        """
        from tyler.storage import get_file_store
        
        if self.file_id:
            file_store = get_file_store()
            return await file_store.get(self.file_id, storage_path=self.storage_path)
            
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            try:
                return base64.b64decode(self.content)
            except:
                # If not base64, try encoding as UTF-8
                return self.content.encode('utf-8')
                
        raise ValueError("No content available - attachment has neither file_id nor content")

    async def ensure_stored(self, force: bool = False) -> None:
        """Ensure content is stored in file storage if needed
        
        Args:
            force: If True, stores content even if already stored
        """
        if (not self.file_id or force) and self.content is not None:
            from tyler.storage import get_file_store
            file_store = get_file_store()
            
            # Get content as bytes
            content = await self.get_content_bytes() if isinstance(self.content, bytes) else self.content.encode('utf-8')
            
            # Save to file storage
            file_metadata = await file_store.save(
                content=content,
                filename=self.filename,
                mime_type=self.mime_type
            )
            
            # Update attachment with storage info
            self.file_id = file_metadata['id']
            self.storage_path = file_metadata['storage_path']
            self.storage_backend = file_metadata['storage_backend']
            # Clear content field since it's now stored
            self.content = None 