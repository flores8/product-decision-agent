import os
import weave
from typing import Dict, Any, Optional
from pathlib import Path
from tyler.storage.file_store import FileStore
from tyler.utils.file_processor import FileProcessor

@weave.op(name="read-file")
async def read_file(*, 
    file_url: str,
    mime_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Read and extract content from a file.

    Args:
        file_url: Full path to the file
        mime_type: Optional MIME type hint for file processing

    Returns:
        Dict[str, Any]: Dictionary containing the extracted content and metadata
    """
    try:
        # Use the file_url directly as the path
        file_path = Path(file_url)
            
        if not file_path.exists():
            raise FileNotFoundError(f"File not found at {file_path}")
            
        # Read file content
        content = file_path.read_bytes()
        
        # Process the file using the FileProcessor
        processor = FileProcessor()
        result = processor.process_file(content, file_path.name)
        
        # Add file URL to the result
        result["file_url"] = file_url
        
        return result

    except Exception as e:
        return {
            "error": str(e),
            "file_url": file_url
        }

# Define the tools list
TOOLS = [
    {
        "definition": {
            "type": "function",
            "function": {
                "name": "read-file",
                "description": "Reads and extracts content from files. Can handle text files, PDFs, and other document formats.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_url": {
                            "type": "string",
                            "description": "URL or path to the file"
                        },
                        "mime_type": {
                            "type": "string",
                            "description": "Optional MIME type hint for file processing",
                            "default": None
                        }
                    },
                    "required": ["file_url"]
                }
            }
        },
        "implementation": read_file
    }
] 