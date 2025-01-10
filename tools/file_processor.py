import os
import magic
import base64
from typing import Dict, Any, Optional, List
from openai import OpenAI
import io
from PIL import Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes

class FileProcessor:
    def __init__(self):
        self.supported_types = {
            'application/pdf': self._process_pdf,
            'image/jpeg': self._process_image,
            'image/png': self._process_image,
            'image/gif': self._process_image,
            'image/webp': self._process_image,
        }
        self.client = OpenAI()

    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process a file and extract its text content using AI
        
        Args:
            file_content (bytes): The binary content of the file
            filename (str): Original filename
            
        Returns:
            Dict[str, Any]: Dictionary containing extracted text and metadata
        """
        mime_type = magic.from_buffer(file_content, mime=True)
        
        # Special handling for PDFs that might be detected as text/plain
        if mime_type == "text/plain" and filename.lower().endswith('.pdf'):
            print("File has .pdf extension, treating as PDF")
            return self._process_pdf(file_content)
            
        if mime_type not in self.supported_types:
            return {
                "error": f"Unsupported file type: {mime_type}. Currently supporting PDFs and images (JPEG, PNG, GIF, WebP)",
                "supported_types": list(self.supported_types.keys())
            }
            
        processor = self.supported_types[mime_type]
        return processor(file_content)

    def _process_pdf(self, content: bytes) -> Dict[str, Any]:
        """Process PDF file using text extraction first, falling back to Vision API if needed"""
        try:
            # Try text extraction first
            pdf = PdfReader(io.BytesIO(content))
            pages = []
            empty_pages = []
            
            # Extract text from each page
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text.strip():  # If page has text content
                    pages.append(f"--- Page {i} ---\n{text}")
                else:
                    empty_pages.append(i)
                    
            # If we have any text content, process it
            if pages:
                text_content = "\n\n".join(pages)
                
                # If we have some empty pages, process them with Vision API
                vision_content = ""
                if empty_pages:
                    vision_content = self._process_pdf_pages_with_vision(content, empty_pages)
                
                return {
                    "text": text_content,
                    "vision_text": vision_content,
                    "type": "pdf",
                    "pages": len(pdf.pages),
                    "empty_pages": empty_pages
                }
            
            # If no text was extracted, process the entire PDF with Vision API
            return self._process_pdf_with_vision(content)
            
        except Exception as e:
            return {"error": f"Failed to process PDF: {str(e)}"}

    def _process_pdf_with_vision(self, content: bytes) -> Dict[str, Any]:
        """Process entire PDF using Vision API"""
        try:
            # Convert PDF to images
            images = convert_from_bytes(content)
            pages_text = []
            
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
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract all text from this page, preserving the structure and layout. Include any relevant formatting or visual context that helps understand the text organization."
                                },
                                {
                                    "type": "image",
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
                
                pages_text.append(f"--- Page {i} ---\n{response.choices[0].message.content}")
            
            return {
                "text": "\n\n".join(pages_text),
                "type": "pdf",
                "pages": len(images),
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
                        model="gpt-4-vision-preview",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Extract all text from this page, preserving the structure and layout. Include any relevant formatting or visual context that helps understand the text organization."
                                    },
                                    {
                                        "type": "image",
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
                    
                    pages_text.append(f"--- Page {page_num} ---\n{response.choices[0].message.content}")
            
            return "\n\n".join(pages_text)
            
        except Exception as e:
            return f"Failed to process PDF pages with Vision API: {str(e)}"

    def _process_image(self, content: bytes) -> Dict[str, Any]:
        """Process image file using GPT-4 Vision"""
        try:
            # Open image to get metadata and ensure it's in a supported format
            image = Image.open(io.BytesIO(content))
            
            # Convert to base64
            b64_image = base64.b64encode(content).decode('utf-8')
            
            # First, get a high-level analysis of the image
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this image and tell me:\n1. What type of document or image is this?\n2. What is the main content or purpose?\n3. Are there any dates, numbers, or key information visible?"
                            },
                            {
                                "type": "image",
                                "image_url": {
                                    "url": f"data:image/{image.format.lower()};base64,{b64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
            )
            
            overview = response.choices[0].message.content

            # Then, get detailed text extraction
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this image, preserving the structure and layout. Include any relevant formatting or visual context that helps understand the text organization."
                            },
                            {
                                "type": "image",
                                "image_url": {
                                    "url": f"data:image/{image.format.lower()};base64,{b64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0.2
            )
            
            detailed_text = response.choices[0].message.content
            
            return {
                "overview": overview,
                "text": detailed_text,
                "type": "image",
                "size": image.size,
                "format": image.format
            }
        except Exception as e:
            return {"error": f"Failed to process image: {str(e)}"}

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