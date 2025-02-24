from typing import Dict, Optional, Any, Union, Literal
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
    status: Literal["pending", "stored", "failed"] = "pending"

    def model_dump(self) -> Dict[str, Any]:
        """Convert attachment to a dictionary suitable for JSON serialization"""
        data = {
            "filename": self.filename,
            "mime_type": self.mime_type,
            "processed_content": self.processed_content,
            "file_id": self.file_id,
            "storage_path": self.storage_path,
            "storage_backend": self.storage_backend,
            "status": self.status
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

    async def process(self) -> None:
        """Process the attachment content using the file processor.
        
        This method attempts to process the attachment content using the file processor.
        If processing fails, the processed_content will be set to None.
        """
        from tyler.utils.file_processor import process_file
        
        try:
            if self.content is not None:
                content_bytes = await self.get_content_bytes()
                
                # Process all files consistently
                self.processed_content = await process_file(content_bytes, self.filename, self.mime_type)
                
                # Preserve any existing description
                if hasattr(self, "processed_content") and self.processed_content and self.processed_content.get("description"):
                    if not self.processed_content:
                        self.processed_content = {}
                    self.processed_content["description"] = self.processed_content.get("description")
            else:
                self.processed_content = None
        except Exception as e:
            self.processed_content = None
            raise e

    def update_processed_content_with_url(self) -> None:
        """Update processed_content with URL after storage_path is set.
        
        This should be called after ensure_stored() to add the URL to processed_content.
        """
        if self.storage_path:
            if not self.processed_content:
                self.processed_content = {}
            self.processed_content["url"] = f"/files/{self.storage_path}"

    async def ensure_stored(self, force: bool = False) -> None:
        """Ensure the attachment is stored in the configured storage backend.
        
        Args:
            force: If True, stores the attachment even if already stored
            
        Raises:
            RuntimeError: If attachment has no content or storage fails
        """
        if not self.file_id or force:
            from tyler.storage import get_file_store
            
            store = get_file_store()
            if self.content is None:
                self.status = "failed"
                raise RuntimeError(f"Cannot store attachment {self.filename}: no content provided")
                
            try:
                # Convert content to bytes if it's a base64 string
                content_to_store = self.content
                if isinstance(content_to_store, str):
                    try:
                        content_to_store = base64.b64decode(content_to_store)
                    except:
                        # If not base64, encode as UTF-8
                        content_to_store = content_to_store.encode('utf-8')
                
                result = await store.save(content_to_store, self.filename)
                self.file_id = result['id']
                self.storage_backend = result['storage_backend']
                self.storage_path = result['storage_path']
                self.status = "stored"
                
                # Update processed_content with URL after storage
                self.update_processed_content_with_url()
            except Exception as e:
                self.status = "failed"
                raise RuntimeError(f"Failed to store attachment {self.filename}: {str(e)}") from e 