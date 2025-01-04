import os
import streamlit as st
from typing import Dict, List, Optional
import requests
import json
import weave

NOTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "notion-search",
            "description": "Searches all titles of pages and databases in Notion that have been shared with the integration. Can search by title or filter to only pages/databases.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find in page/database titles. If no results are found, try rephrasing the query around subject matter such that it likely will be in the title. Optional - if not provided returns all pages/databases."
                    },
                    "filter": {
                        "type": "object",
                        "description": "Filter to only return pages or databases. Optional.",
                        "properties": {
                            "value": {
                                "type": "string",
                                "enum": ["page", "database"]
                            },
                            "property": {
                                "type": "string",
                                "enum": ["object"]
                            }
                        }
                    },
                    "start_cursor": {
                        "type": "string",
                        "description": "If there are more results, pass this cursor to fetch the next page. Optional."
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Number of results to return. Default 100. Optional.",
                        "minimum": 1,
                        "maximum": 100
                    }
                }
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "notion-get_page",
            "description": "Retrieves a Notion page by its ID. Returns the page properties and metadata, not the content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page to retrieve"
                    }
                },
                "required": ["page_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notion-get_page_content",
            "description": "Retrieves the content (blocks) of a Notion page by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page whose content to retrieve"
                    },
                    "start_cursor": {
                        "type": "string",
                        "description": "If there are more blocks, pass this cursor to fetch the next page. Optional."
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Number of blocks to return. Default 100. Optional.",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["page_id"]
            }
        }
    }
]

class NotionClient:
    def __init__(self):
        # Try environment variable first, then streamlit secrets
        self.token = os.environ.get("NOTION_TOKEN") or st.secrets.get("NOTION_TOKEN")
        if not self.token:
            raise ValueError("NOTION_TOKEN environment variable is required")
        
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Makes a request to the Notion API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            error_msg = f"Notion API request failed: {str(e)}"
            if hasattr(e.response, 'json'):
                error_msg += f"\nResponse: {e.response.json()}"
            raise Exception(error_msg)

@weave.op(name="notion-search")
def search(*, 
          query: Optional[str] = None,
          filter: Optional[Dict] = None,
          start_cursor: Optional[str] = None,
          page_size: Optional[int] = None) -> Dict:
    """
    Searches Notion pages and databases.
    """
    client = NotionClient()
    
    data = {}
    if query:
        data["query"] = query
    if filter:
        data["filter"] = filter
    if start_cursor:
        data["start_cursor"] = start_cursor
    if page_size:
        data["page_size"] = page_size
        
    return client._make_request("POST", "search", data)

@weave.op(name="notion-get_page")
def get_page(*, page_id: str) -> Dict:
    """
    Retrieves a page from Notion by its ID.
    """
    client = NotionClient()
    return client._make_request("GET", f"pages/{page_id}") 

@weave.op(name="notion-get_page_content")
def get_page_content(*, 
                    page_id: str,
                    start_cursor: Optional[str] = None,
                    page_size: Optional[int] = None) -> Dict:
    """
    Retrieves the content (blocks) of a Notion page.
    """
    client = NotionClient()
    
    endpoint = f"blocks/{page_id}/children"
    data = {}
    
    if start_cursor:
        data["start_cursor"] = start_cursor
    if page_size:
        data["page_size"] = page_size
        
    return client._make_request("GET", endpoint, data) 