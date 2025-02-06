from typing import Dict, Optional, Literal, Any, Union, List, TypedDict
from datetime import datetime, UTC
from pydantic import BaseModel, Field, field_validator
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
    sequence: Optional[int] = Field(
        default=None,
        description="Message sequence number within thread. System messages get lowest sequences."
    )
    content: Optional[Union[str, List[Union[TextContent, ImageContent]]]] = None
    name: Optional[str] = None
    tool_call_id: Optional[str] = None  # Required for tool messages
    tool_calls: Optional[list] = None  # For assistant messages
    attributes: Dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: Optional[Dict[str, Any]] = None  # {"name": "slack", "thread_id": "..."}
    attachments: List[Attachment] = Field(default_factory=list)
    
    # Simple metrics structure
    metrics: Dict[str, Any] = Field(
        default_factory=lambda: {
            "model": None,
            "timing": {
                "started_at": None,
                "ended_at": None,
                "latency": 0
            },
            "usage": {
                "completion_tokens": 0,
                "prompt_tokens": 0,
                "total_tokens": 0
            },
            "weave_call": {
                "id": "",
                "trace_id": "",
                "project_id": "",
                "request_id": ""
            }
        }
    )

    @field_validator("timestamp", mode="before")
    def ensure_timezone(cls, value: datetime) -> datetime:
        """Ensure timestamp is timezone-aware UTC"""
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

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
                "sequence": self.sequence,  # Include sequence in hash
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

    def _serialize_tool_calls(self, tool_calls):
        """Helper method to serialize tool calls into a JSON-friendly format"""
        if not tool_calls:
            return None
            
        serialized_calls = []
        for call in tool_calls:
            try:
                # Handle OpenAI response objects
                if hasattr(call, 'model_dump'):
                    # For newer Pydantic models
                    call_dict = call.model_dump()
                elif hasattr(call, 'to_dict'):
                    # For objects with to_dict method
                    call_dict = call.to_dict()
                elif hasattr(call, 'id') and hasattr(call, 'function'):
                    # Direct access to OpenAI tool call attributes
                    call_dict = {
                        "id": call.id,
                        "type": getattr(call, 'type', 'function'),
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments
                        }
                    }
                elif isinstance(call, dict):
                    # If it's already a dict, ensure it has the required structure
                    call_dict = {
                        "id": call.get("id"),
                        "type": call.get("type", "function"),
                        "function": {
                            "name": call.get("function", {}).get("name"),
                            "arguments": call.get("function", {}).get("arguments")
                        }
                    }
                else:
                    logger.warning(f"Unsupported tool call format: {type(call)}")
                    continue

                # Validate the required fields are present
                if all(key in call_dict for key in ["id", "type", "function"]):
                    serialized_calls.append(call_dict)
                else:
                    logger.warning(f"Missing required fields in tool call: {call_dict}")
            except Exception as e:
                logger.error(f"Error serializing tool call: {str(e)}")
                continue
                
        return serialized_calls

    def model_dump(self) -> Dict[str, Any]:
        """Convert message to a dictionary suitable for JSON serialization"""
        message_dict = {
            "id": self.id,
            "role": self.role,
            "sequence": self.sequence,  # Include sequence in serialization
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "metrics": self.metrics
        }
        
        if self.name:
            message_dict["name"] = self.name
            
        if self.tool_call_id:
            message_dict["tool_call_id"] = self.tool_call_id
            
        if self.tool_calls:
            message_dict["tool_calls"] = self._serialize_tool_calls(self.tool_calls)
            
        if self.attributes:
            message_dict["attributes"] = self.attributes

        if self.attachments:
            message_dict["attachments"] = [attachment.model_dump() for attachment in self.attachments]
            
        return message_dict
        
    def to_chat_completion_message(self) -> Dict[str, Any]:
        """Return message in the format expected by chat completion APIs"""
        message_dict = {
            "role": self.role,
            "content": self.content if self.content is not None else "",  # Keep content as is for multimodal messages
            "sequence": self.sequence  # Add sequence for consistency
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
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "role": "user",
                    "sequence": 1,
                    "content": "Here are some files to look at",
                    "name": None,
                    "tool_call_id": None,
                    "tool_calls": None,
                    "attributes": {},
                    "timestamp": "2024-02-07T00:00:00+00:00",
                    "source": {
                        "name": "slack",
                        "thread_id": "1234567890.123456"
                    },
                    "attachments": [
                        {
                            "filename": "document.pdf",
                            "content": "base64_encoded_content_string",
                            "mime_type": "application/pdf",
                            "processed_content": {
                                "type": "document",
                                "text": "Extracted text content from PDF",
                                "overview": "Brief summary of the document"
                            }
                        },
                        {
                            "filename": "screenshot.png",
                            "content": "base64_encoded_image_string",
                            "mime_type": "image/png",
                            "processed_content": {
                                "type": "image",
                                "text": "OCR extracted text if applicable",
                                "overview": "Description of image contents",
                                "analysis": {
                                    "objects": ["person", "desk", "computer"],
                                    "text_detected": true,
                                    "dominant_colors": ["blue", "white"]
                                }
                            }
                        },
                        {
                            "filename": "data.json",
                            "content": "eyJrZXkiOiAidmFsdWUifQ==",  # base64 of {"key": "value"}
                            "mime_type": "application/json",
                            "processed_content": {
                                "type": "json",
                                "overview": "JSON data structure containing key-value pairs",
                                "parsed_content": {"key": "value"}
                            }
                        }
                    ],
                    "metrics": {
                        "model": "gpt-4o",
                        "timing": {
                            "started_at": "2024-02-07T00:00:00+00:00",
                            "ended_at": "2024-02-07T00:00:01+00:00",
                            "latency": 1.0
                        },
                        "usage": {
                            "completion_tokens": 100,
                            "prompt_tokens": 50,
                            "total_tokens": 150
                        },
                        "weave_call": {
                            "id": "call-123",
                            "trace_id": "trace-456",
                            "project_id": "proj-789",
                            "request_id": "req-abc"
                        }
                    }
                }
            ]
        }
    } 