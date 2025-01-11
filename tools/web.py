import os
import requests
import weave
from typing import Optional, Dict
from pathlib import Path
from bs4 import BeautifulSoup

WEB_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web-fetch_page",
            "description": "Fetches content from a web page and returns it in a clean, readable format with preserved structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch"
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format - either 'text' or 'html'",
                        "enum": ["text", "html"],
                        "default": "text"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional headers to send with the request"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web-download_file",
            "description": "Downloads a file from a URL and saves it to the downloads directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the file to download"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Optional filename to save as. If not provided, will use the filename from the URL"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Optional headers to send with the request"
                    }
                },
                "required": ["url"]
            }
        }
    }
]

def fetch_html(url: str, headers: Optional[Dict] = None) -> str:
    """
    Fetches the HTML content from the given URL.
    
    Args:
        url (str): The URL to fetch the HTML from
        headers (Dict, optional): Headers to send with the request
    
    Returns:
        str: The HTML content of the page
    
    Raises:
        Exception: If there's an error fetching the URL
    """
    try:
        response = requests.get(url, headers=headers or {}, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        raise Exception(f"Error fetching URL: {e}")

def extract_text_from_html(html_content: str) -> str:
    """
    Extracts clean, readable text from HTML content.
    
    Args:
        html_content (str): The HTML content to parse
    
    Returns:
        str: The extracted text content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script, style, and title elements
    for element in soup(["script", "style", "title"]):
        element.decompose()
    
    # Get text with better spacing
    text = soup.get_text(separator='\n', strip=True)
    
    # Clean up excessive newlines while preserving paragraph structure
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = '\n\n'.join(lines)
    
    return text

@weave.op(name="web-fetch_page")
def fetch_page(*, url: str, format: str = "text", headers: Optional[Dict] = None) -> Dict:
    """
    Fetch content from a web page and return it in the specified format.

    Args:
        url (str): The URL to fetch
        format (str): Output format - either 'text' or 'html'
        headers (Dict, optional): Headers to send with the request

    Returns:
        Dict: Contains status code, content, and any error messages
    """
    try:
        html_content = fetch_html(url, headers)
        
        content = extract_text_from_html(html_content) if format == "text" else html_content
        
        return {
            'success': True,
            'status_code': 200,
            'content': content,
            'content_type': format,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'status_code': None,
            'content': None,
            'content_type': None,
            'error': str(e)
        }

@weave.op(name="web-download_file")
def download_file(*, url: str, filename: str = "", headers: Optional[Dict] = None) -> Dict:
    """
    Download a file from a URL and save it to the downloads directory.

    Args:
        url (str): The URL of the file to download
        filename (str): Optional filename to save as
        headers (Dict, optional): Headers to send with the request

    Returns:
        Dict: Contains download status, file path, content type, and size information
    """
    try:
        # Create downloads directory if it doesn't exist
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)
        
        # Get filename if not provided
        if not filename:
            # Try to get from Content-Disposition first
            response = requests.head(url, headers=headers or {}, timeout=30)
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                import re
                if match := re.search(r'filename="?([^"]+)"?', content_disposition):
                    filename = match.group(1)
            
            # Fall back to URL if still no filename
            if not filename:
                filename = url.split('/')[-1].split('?')[0]  # Remove query parameters
                if not filename:
                    filename = 'downloaded_file'
        
        # Create full file path
        file_path = downloads_dir / filename
        
        # Download the file with streaming
        response = requests.get(url, headers=headers or {}, stream=True, timeout=30)
        response.raise_for_status()
        
        # Get content info
        content_type = response.headers.get('content-type', 'unknown')
        file_size = int(response.headers.get('content-length', 0))
        
        # Write the file
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return {
            'success': True,
            'file_path': str(file_path),
            'content_type': content_type,
            'file_size': file_size,
            'filename': filename,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'file_path': None,
            'content_type': None,
            'file_size': None,
            'filename': None,
            'error': str(e)
        } 