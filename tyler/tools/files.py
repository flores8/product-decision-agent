import os
import weave
from typing import Dict, Any, Optional
from pathlib import Path
import mimetypes
from PyPDF2 import PdfReader
import io
import base64
from pdf2image import convert_from_bytes
from litellm import completion

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
        
        # Detect MIME type if not provided
        if not mime_type:
            mime_type = mimetypes.guess_type(file_path.name)[0]
            if not mime_type:
                # Try to detect from content
                import magic
                mime_type = magic.from_buffer(content, mime=True)

        # Process based on MIME type
        if mime_type == 'application/pdf':
            return await process_pdf(content, file_url)
        elif mime_type.startswith('text/'):
            # For text files, decode and return content
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                # Try other common encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        text_content = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    return {
                        "error": "Could not decode text file with any supported encoding",
                        "file_url": file_url
                    }
            
            return {
                "text": text_content,
                "type": "text",
                "file_url": file_url,
                "mime_type": mime_type
            }
        else:
            return {
                "error": f"Unsupported file type: {mime_type}",
                "file_url": file_url
            }

    except Exception as e:
        return {
            "error": str(e),
            "file_url": file_url
        }

async def process_pdf(content: bytes, file_url: str) -> Dict[str, Any]:
    """Process PDF file using text extraction first, falling back to Vision API if needed"""
    try:
        pdf_reader = PdfReader(io.BytesIO(content))
        text = ""
        empty_pages = []
        
        for i, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if not page_text.strip():
                    empty_pages.append(i + 1)
                text += page_text + "\n"
            except Exception as page_error:
                empty_pages.append(i + 1)
                continue
                
        text = text.strip()
        if not text:
            # If no text was extracted, try processing with vision
            return await process_pdf_with_vision(content, file_url)
            
        return {
            "text": text,
            "type": "pdf",
            "pages": len(pdf_reader.pages),
            "empty_pages": empty_pages,
            "processing_method": "text",
            "file_url": file_url
        }
            
    except Exception as e:
        return {
            "error": f"Failed to process PDF: {str(e)}",
            "file_url": file_url
        }

async def process_pdf_with_vision(content: bytes, file_url: str) -> Dict[str, Any]:
    """Process PDF using Vision API"""
    try:
        # Convert PDF to images
        images = convert_from_bytes(content)
        pages_text = []
        empty_pages = []
        
        for i, image in enumerate(images, 1):
            # Save image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Convert to base64
            b64_image = base64.b64encode(img_byte_arr).decode('utf-8')
            
            # Process with Vision API
            response = completion(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this page, preserving the structure and layout. Include any relevant formatting or visual context that helps understand the text organization."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0.2
            )
            
            page_text = response.choices[0].message.content
            if not page_text.strip():
                empty_pages.append(i)
            pages_text.append(f"--- Page {i} ---\n{page_text}")
        
        return {
            "text": "\n\n".join(pages_text),
            "type": "pdf",
            "pages": len(images),
            "empty_pages": empty_pages,
            "processing_method": "vision",
            "file_url": file_url
        }
            
    except Exception as e:
        return {
            "error": f"Failed to process PDF with Vision API: {str(e)}",
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