import os
import weave
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import base64
from PyPDF2 import PdfReader
import pandas as pd
import json
import csv
from io import StringIO

@weave.op(name="extract-pdf-text")
async def extract_pdf_text(*, 
    file_url: str,
    pages: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Extract text content from a PDF file.

    Args:
        file_url: Full path to the PDF file
        pages: Optional list of specific pages to extract (1-based). If None, extracts all pages.

    Returns:
        Dict containing extracted text and metadata
    """
    try:
        file_path = Path(file_url)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found at {file_path}")

        pdf = PdfReader(file_path)
        total_pages = len(pdf.pages)
        
        # Handle page selection
        if pages:
            # Convert to 0-based indices and validate
            page_indices = [p - 1 for p in pages if 0 < p <= total_pages]
            if not page_indices:
                raise ValueError(f"No valid pages in {pages}. PDF has {total_pages} pages.")
        else:
            page_indices = range(total_pages)

        # Extract text from selected pages
        extracted_text = []
        for i in page_indices:
            page = pdf.pages[i]
            text = page.extract_text()
            extracted_text.append({
                "page": i + 1,
                "content": text.strip()
            })

        return {
            "success": True,
            "pages": extracted_text,
            "total_pages": total_pages,
            "file_url": file_url
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_url": file_url
        }

@weave.op(name="parse-csv")
async def parse_csv(*, 
    file_url: str,
    preview_rows: int = 5,
    delimiter: str = ","
) -> Dict[str, Any]:
    """
    Parse and analyze CSV file content.

    Args:
        file_url: Full path to the CSV file
        preview_rows: Number of rows to include in preview
        delimiter: CSV delimiter character

    Returns:
        Dict containing CSV analysis and preview
    """
    try:
        file_path = Path(file_url)
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found at {file_path}")

        # Read CSV file
        df = pd.read_csv(file_path, delimiter=delimiter)
        
        # Get basic statistics
        stats = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
            "column_types": {col: str(df[col].dtype) for col in df.columns}
        }

        # Generate preview
        preview = df.head(preview_rows).to_dict(orient='records')

        return {
            "success": True,
            "statistics": stats,
            "preview": preview,
            "file_url": file_url
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_url": file_url
        }

@weave.op(name="parse-json")
async def parse_json(*,
    file_url: str,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse and extract data from a JSON file.

    Args:
        file_url: Full path to the JSON file
        path: Optional JSON path to extract specific data (e.g., "data.items[0].name")

    Returns:
        Dict containing parsed JSON data
    """
    try:
        file_path = Path(file_url)
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found at {file_path}")

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Extract specific path if provided
        if path:
            try:
                parts = path.split('.')
                current = data
                for part in parts:
                    if '[' in part:
                        # Handle array indexing
                        name, index = part.split('[')
                        index = int(index.rstrip(']'))
                        current = current[name][index]
                    else:
                        current = current[part]
                data = current
            except (KeyError, IndexError) as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON path: {str(e)}",
                    "file_url": file_url
                }

        return {
            "success": True,
            "data": data,
            "file_url": file_url
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON format: {str(e)}",
            "file_url": file_url
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_url": file_url
        }

# Define the tools list
TOOLS = [
    {
        "definition": {
            "type": "function",
            "function": {
                "name": "extract-pdf-text",
                "description": "Extract text content from PDF files. Can extract from specific pages or the entire document.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_url": {
                            "type": "string",
                            "description": "Full path to the PDF file"
                        },
                        "pages": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Optional list of specific pages to extract (1-based). If not provided, extracts all pages.",
                            "default": None
                        }
                    },
                    "required": ["file_url"]
                }
            }
        },
        "implementation": extract_pdf_text
    },
    {
        "definition": {
            "type": "function",
            "function": {
                "name": "parse-csv",
                "description": "Parse and analyze CSV files. Provides statistics and a preview of the data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_url": {
                            "type": "string",
                            "description": "Full path to the CSV file"
                        },
                        "preview_rows": {
                            "type": "integer",
                            "description": "Number of rows to include in preview",
                            "default": 5
                        },
                        "delimiter": {
                            "type": "string",
                            "description": "CSV delimiter character",
                            "default": ","
                        }
                    },
                    "required": ["file_url"]
                }
            }
        },
        "implementation": parse_csv
    },
    {
        "definition": {
            "type": "function",
            "function": {
                "name": "parse-json",
                "description": "Parse and extract data from JSON files. Can extract specific data using JSON path.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_url": {
                            "type": "string",
                            "description": "Full path to the JSON file"
                        },
                        "path": {
                            "type": "string",
                            "description": "Optional JSON path to extract specific data (e.g., 'data.items[0].name')",
                            "default": None
                        }
                    },
                    "required": ["file_url"]
                }
            }
        },
        "implementation": parse_json
    }
] 