"""File processing utilities"""
import os
import tempfile
from pathlib import Path
import mimetypes
import logging
from PyPDF2 import PdfReader
from typing import Optional, Dict, Any, List, Tuple, Union
import json
import hashlib
import base64
from datetime import datetime, UTC
from openai import OpenAI
import io
from PIL import Image
from pdf2image import convert_from_bytes

logger = logging.getLogger(__name__)

# Set PyPDF2 to only log errors
logging.getLogger('PyPDF2').setLevel(logging.ERROR)

class FileProcessor:
    def __init__(self):
        self.supported_types = {
            'application/pdf': self._process_pdf,
        }
        self.client = OpenAI()

    def _format_message_content(self, text_content: str, image_data: Optional[Dict] = None) -> Union[str, List[Dict]]:
        """
        Format message content based on whether it includes an image
        
        Args:
            text_content (str): The text content of the message
            image_data (Dict, optional): Image data if present
            
        Returns:
            Union[str, List[Dict]]: Formatted content
        """
        if image_data is None:
            return text_content
            
        return json.dumps([
            {
                "type": "text",
                "text": text_content
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_data['mime_type']};base64,{image_data['content']}"
                }
            }
        ])

    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process a file and extract its text content using AI
        
        Args:
            file_content (bytes): The binary content of the file
            filename (str): Original filename
            
        Returns:
            Dict[str, Any]: Dictionary containing extracted text and metadata
        """
        mime_type = mimetypes.guess_type(filename)[0]
        
        # Special handling for PDFs that might be detected as text/plain
        if mime_type == "text/plain" and filename.lower().endswith('.pdf'):
            print("File has .pdf extension, treating as PDF")
            return self._process_pdf(file_content)
            
        if mime_type not in self.supported_types:
            return {
                "error": f"Unsupported file type: {mime_type}. Currently supporting PDFs only.",
                "supported_types": list(self.supported_types.keys())
            }
            
        processor = self.supported_types[mime_type]
        return processor(file_content)

    def _process_pdf(self, content: bytes) -> Dict[str, Any]:
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
                    logger.warning(f"Error extracting text from page {i}: {str(page_error)}")
                    empty_pages.append(i + 1)
                    continue
                    
            text = text.strip()
            if not text:
                # If no text was extracted, try processing with vision
                return self._process_pdf_with_vision(content)
                
            return {
                "text": text,
                "type": "pdf",
                "pages": len(pdf_reader.pages),
                "empty_pages": empty_pages,
                "processing_method": "text"
            }
            
        except Exception as e:
            logger.error(f"Failed to process PDF: {str(e)}")
            raise

    def _process_pdf_with_vision(self, content: bytes) -> Dict[str, Any]:
        """Process entire PDF using Vision API"""
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
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": self._format_message_content(
                                "Extract all text from this page, preserving the structure and layout. Include any relevant formatting or visual context that helps understand the text organization.",
                                {"mime_type": "image/png", "content": b64_image}
                            )
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
                "processing_method": "vision"
            }
            
        except Exception as e:
            return {"error": f"Failed to process PDF with Vision API: {str(e)}"}

    def _process_pdf_pages_with_vision(self, content: bytes, page_numbers: List[int]) -> str:
        """Process specific PDF pages using Vision API"""
        try:
            # Convert PDF to images
            images = convert_from_bytes(content)
            pages_text = []
            
            for page_num in page_numbers:
                if page_num <= len(images):
                    image = images[page_num - 1]
                    
                    # Save image to bytes
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    # Convert to base64
                    b64_image = base64.b64encode(img_byte_arr).decode('utf-8')
                    
                    # Process with Vision API
                    response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": self._format_message_content(
                                    "Extract all text from this page, preserving the structure and layout. Include any relevant formatting or visual context that helps understand the text organization.",
                                    {"mime_type": "image/png", "content": b64_image}
                                )
                            }
                        ],
                        max_tokens=4096,
                        temperature=0.2
                    )
                    
                    pages_text.append(f"--- Page {page_num} ---\n{response.choices[0].message.content}")
            
            return "\n\n".join(pages_text)
            
        except Exception as e:
            return f"Failed to process PDF pages with Vision API: {str(e)}"

def process_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Tool function to process files and extract text/information
    
    Args:
        file_content (bytes): The binary content of the file
        filename (str): Name of the file being processed
        
    Returns:
        Dict[str, Any]: Extracted information from the file
    """
    processor = FileProcessor()
    return processor.process_file(file_content, filename) 