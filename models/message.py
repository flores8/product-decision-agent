from typing import Dict, Optional, Literal, Any, Union, List, TypedDict
from datetime import datetime
from pydantic import BaseModel, Field
import hashlib
import json
import logging
from base64 import b64encode
import base64

logger = logging.getLogger(__name__)

class Attachment(BaseModel):
    """Represents a file attached to a message"""
    filename: str
    content: Union[bytes, str]  # Can be either bytes or base64 string
    mime_type: Optional[str] = None
    processed_content: Optional[Dict[str, Any]] = None

    def model_dump(self) -> Dict[str, Any]:
        """Convert attachment to a dictionary suitable for JSON serialization"""
        data = {
            "filename": self.filename,
            "mime_type": self.mime_type,
            "processed_content": self.processed_content
        }
        # Convert bytes to base64 string for JSON serialization
        if isinstance(self.content, bytes):
            data["content"] = b64encode(self.content).decode('utf-8')
        else:
            data["content"] = self.content
        return data
        
    def get_content_bytes(self) -> bytes:
        """Get the content as bytes, converting from base64 if necessary"""
        if isinstance(self.content, bytes):
            return self.content
        elif isinstance(self.content, str):
            try:
                return base64.b64decode(self.content)
            except:
                # If not base64, try encoding as UTF-8
                return self.content.encode('utf-8')
        raise ValueError("Content must be either bytes or string")

class ImageUrl(TypedDict):
    url: str

class ImageContent(TypedDict):
    type: Literal["image_url"]
    image_url: ImageUrl

class TextContent(TypedDict):
    type: Literal["text"]
    text: str

class Message(BaseModel):
    """Represents a single message in a thread"""
    id: str = None  # Will be set in __init__
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[Union[str, List[Union[TextContent, ImageContent]]]] = None
    name: Optional[str] = None
    tool_call_id: Optional[str] = None  # Required for tool messages
    tool_calls: Optional[list] = None  # For assistant messages
    attributes: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[Dict[str, Any]] = None  # {"name": "slack", "thread_id": "..."}
    attachments: List[Attachment] = Field(default_factory=list)

    def __init__(self, **data):
        # Handle file content if provided as raw bytes
        if "file_content" in data and "filename" in data:
            if "attachments" not in data:
                data["attachments"] = []
            data["attachments"].append(Attachment(
                filename=data.pop("filename"),
                content=data.pop("file_content")
            ))
        
        super().__init__(**data)
        if not self.id:
            # Create a hash of relevant properties
            hash_content = {
                "role": self.role,
                "content": self.content,
                "timestamp": self.timestamp.isoformat()
            }
            # Include name for function messages
            if self.name and self.role == "tool":
                hash_content["name"] = self.name
                
            if self.source:
                hash_content["source"] = self.source
            
            # Create deterministic JSON string for hashing
            hash_str = json.dumps(hash_content, sort_keys=True)
            self.id = hashlib.sha256(hash_str.encode()).hexdigest()
            logger.debug(f"Generated message ID {self.id} from hash content: {hash_str}")

    def model_dump(self) -> Dict[str, Any]:
        """Convert message to a dictionary suitable for JSON serialization"""
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "name": self.name,
            "tool_call_id": self.tool_call_id,
            "tool_calls": self.tool_calls,
            "attributes": self.attributes,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "attachments": [attachment.model_dump() for attachment in self.attachments]
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to a dictionary suitable for JSON serialization"""
        message_dict = {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }
        
        if self.name:
            message_dict["name"] = self.name
            
        if self.attributes:
            message_dict["attributes"] = self.attributes

        if self.attachments:
            message_dict["attachments"] = [
                {
                    "filename": f.filename,
                    "mime_type": f.mime_type,
                    "processed_content": f.processed_content
                }
                for f in self.attachments
            ]
            
        return message_dict
        
    def to_chat_completion_message(self) -> Dict[str, Any]:
        """Return message in the format expected by chat completion APIs"""
        message_dict = {
            "role": self.role,
            "content": self.content if self.content is not None else ""  # Keep content as is for multimodal messages
        }
        
        if self.name:
            message_dict["name"] = self.name
            
        if self.role == "assistant" and self.tool_calls:
            message_dict["tool_calls"] = self.tool_calls
            
        if self.role == "tool" and self.tool_call_id:
            message_dict["tool_call_id"] = self.tool_call_id

        # Only append file contents if content is a string
        if self.attachments and isinstance(self.content, str):
            file_contents = []
            for f in self.attachments:
                if f.processed_content:
                    file_contents.append(f"\n--- File: {f.filename} ---")
                    if "overview" in f.processed_content:
                        file_contents.append(f"Overview: {f.processed_content['overview']}")
                    if "text" in f.processed_content:
                        file_contents.append(f"Content:\n{f.processed_content['text']}")
                    if "error" in f.processed_content:
                        file_contents.append(f"Error: {f.processed_content['error']}")
            
            if file_contents:
                if message_dict["content"]:
                    message_dict["content"] += "\n\n" + "\n".join(file_contents)
                else:
                    message_dict["content"] = "\n".join(file_contents)

        return message_dict

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "role": "user",
                    "content": "Hello, how are you?",
                    "name": None,
                    "attributes": {},
                    "source": {
                        "name": "slack",
                        "thread_id": "1234567890.123456"
                    }
                }
            ]
        }
    } 