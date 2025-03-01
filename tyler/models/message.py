from typing import Dict, Optional, Literal, Any, Union, List, TypedDict
from datetime import datetime, UTC
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib
import json
from tyler.utils.logging import get_logger
import base64
from .attachment import Attachment
from tyler.storage.file_store import FileStore

# Get configured logger
logger = get_logger(__name__)

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
                "latency": 0  # in milliseconds
            },
            "usage": {
                "completion_tokens": 0,
                "prompt_tokens": 0,
                "total_tokens": 0
            },
            "weave_call": {
                "id": "",
                "ui_url": ""
            }
        }
    )

    @field_validator("timestamp", mode="before")
    def ensure_timezone(cls, value: datetime) -> datetime:
        """Ensure timestamp is timezone-aware UTC"""
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value

    @field_validator("role")
    def validate_role(cls, v):
        """Validate role field"""
        if v not in ["system", "user", "assistant", "tool"]:
            raise ValueError("Invalid role. Must be one of: system, user, assistant, tool")
        return v

    @model_validator(mode='after')
    def validate_tool_message(self):
        """Validate tool message requirements"""
        if self.role == "tool" and not self.tool_call_id:
            raise ValueError("tool_call_id is required for tool messages")
        return self

    @field_validator("tool_calls")
    def validate_tool_calls(cls, v, info):
        """Validate tool_calls field"""
        if v is not None:
            for tool_call in v:
                if not isinstance(tool_call, dict):
                    raise ValueError("Each tool call must be a dictionary")
                if "id" not in tool_call or "type" not in tool_call or "function" not in tool_call:
                    raise ValueError("Tool calls must have id, type, and function fields")
                if not isinstance(tool_call["function"], dict):
                    raise ValueError("Tool call function must be a dictionary")
                if "name" not in tool_call["function"] or "arguments" not in tool_call["function"]:
                    raise ValueError("Tool call function must have name and arguments fields")
        return v

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
            message_dict["attachments"] = []
            for attachment in self.attachments:
                # Ensure content is properly serialized
                attachment_dict = {
                    "filename": attachment.filename,
                    "mime_type": attachment.mime_type,
                }
                if attachment.processed_content:
                    attachment_dict["processed_content"] = attachment.processed_content
                # Only include content if it's already a string (base64)
                if isinstance(attachment.content, str):
                    attachment_dict["content"] = attachment.content
                elif isinstance(attachment.content, bytes):
                    # Convert bytes to base64 if needed
                    attachment_dict["content"] = base64.b64encode(attachment.content).decode('utf-8')
                message_dict["attachments"].append(attachment_dict)
            
        return message_dict
        
    def to_chat_completion_message(self) -> Dict[str, Any]:
        """Return message in the format expected by chat completion APIs"""
        base_content = self.content if isinstance(self.content, str) else ""
        
        message_dict = {
            "role": self.role,
            "content": base_content,
            "sequence": self.sequence
        }
        
        if self.name:
            message_dict["name"] = self.name
            
        if self.role == "assistant" and self.tool_calls:
            message_dict["tool_calls"] = self.tool_calls
            
        if self.role == "tool" and self.tool_call_id:
            message_dict["tool_call_id"] = self.tool_call_id

        # Handle attachments if we have them
        if self.attachments:
            # For user messages, include file references in the content
            if self.role == "user":
                file_references = []
                base_path = FileStore.get_default_path()
                
                for attachment in self.attachments:
                    if not attachment.storage_path:
                        continue
                        
                    # Format file reference with full storage path
                    full_path = base_path / attachment.storage_path
                    file_ref = f"[File: {attachment.filename} ({attachment.mime_type}) | Path: {full_path}]"
                    file_references.append(file_ref)
                
                if file_references:
                    if message_dict["content"]:
                        message_dict["content"] += "\n\n" + "\n".join(file_references)
                    else:
                        message_dict["content"] = "\n".join(file_references)
            
            elif self.role == "assistant":
                # For assistant messages, only include metadata about attachments
                file_info = []
                for f in self.attachments:
                    file_info.append(f"- {f.filename} ({f.mime_type})")
                if file_info and isinstance(message_dict["content"], str):
                    if message_dict["content"]:
                        message_dict["content"] += "\n\nGenerated Files:\n" + "\n".join(file_info)
                    else:
                        message_dict["content"] = "Generated Files:\n" + "\n".join(file_info)
        
        return message_dict

    def add_attachment(self, attachment: Union[Attachment, bytes], filename: Optional[str] = None) -> None:
        """Add an attachment to the message.
        
        Args:
            attachment: Either an Attachment object or raw bytes
            filename: Required if attachment is bytes, ignored if attachment is Attachment
        
        Raises:
            ValueError: If attachment is bytes and filename is not provided
        """
        if isinstance(attachment, Attachment):
            self.attachments.append(attachment)
        elif isinstance(attachment, bytes):
            if not filename:
                raise ValueError("filename is required when adding raw bytes as attachment")
            att = Attachment(
                filename=filename,
                content=attachment
            )
            self.attachments.append(att)
        else:
            raise ValueError("attachment must be either Attachment object or bytes")

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
                                    "text_detected": True,
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
                            "ui_url": "https://weave.ui/call-123"
                        }
                    }
                }
            ]
        },
        "extra": "forbid",
        "validate_assignment": True
    } 