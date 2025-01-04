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
    },
    {
        "type": "function",
        "function": {
            "name": "notion-create_comment",
            "description": "Creates a comment in a Notion page or existing discussion thread.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "The ID of the page to add the comment to. Required if discussion_id is not provided."
                    },
                    "discussion_id": {
                        "type": "string",
                        "description": "The ID of the discussion thread to add the comment to. Required if page_id is not provided."
                    },
                    "rich_text": {
                        "type": "array",
                        "description": "The rich text content of the comment",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {
                                    "type": "object",
                                    "properties": {
                                        "content": {
                                            "type": "string",
                                            "description": "The text content"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notion-get_comments",
            "description": "Retrieves comments from a block ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "block_id": {
                        "type": "string",
                        "description": "The ID of the block to get comments from"
                    },
                    "start_cursor": {
                        "type": "string",
                        "description": "If there are more comments, pass this cursor to fetch the next page. Optional."
                    },
                    "page_size": {
                        "type": "integer",
                        "description": "Number of comments to return. Default 100. Optional.",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["block_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notion-create_page",
            "description": "Creates a new page in Notion as a child of an existing page or database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "parent": {
                        "type": "object",
                        "description": "The parent page or database this page belongs to",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["page_id", "database_id"],
                                "description": "Whether this is a page or database parent"
                            },
                            "id": {
                                "type": "string",
                                "description": "The ID of the parent page or database"
                            }
                        },
                        "required": ["type", "id"]
                    },
                    "properties": {
                        "type": "object",
                        "description": "Page properties. If parent is a page, only title is valid. If parent is a database, keys must match database properties."
                    },
                    "children": {
                        "type": "array",
                        "description": "Page content as an array of block objects. Optional.",
                        "items": {
                            "type": "object"
                        }
                    },
                    "icon": {
                        "type": "object",
                        "description": "Page icon. Optional.",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["emoji", "external"]
                            },
                            "emoji": {
                                "type": "string"
                            },
                            "external": {
                                "type": "object",
                                "properties": {
                                    "url": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    },
                    "cover": {
                        "type": "object",
                        "description": "Page cover image. Optional.",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["external"]
                            },
                            "external": {
                                "type": "object",
                                "properties": {
                                    "url": {
                                        "type": "string"
                                    }
                                }
                            }
                        }
                    }
                },
                "required": ["parent", "properties"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "notion-update_block",
            "description": "Updates the content of a specific block in Notion based on the block type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "block_id": {
                        "type": "string",
                        "description": "The ID of the block to update"
                    },
                    "block_type": {
                        "type": "string",
                        "description": "The type of block being updated (e.g. paragraph, heading_1, to_do, etc)"
                    },
                    "content": {
                        "type": "object",
                        "description": "The new content for the block, structured according to the block type"
                    }
                },
                "required": ["block_id", "block_type", "content"]
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
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
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

@weave.op(name="notion-create_comment")
def create_comment(*, 
                  page_id: Optional[str] = None,
                  discussion_id: Optional[str] = None,
                  rich_text: List[Dict]) -> Dict:
    """
    Creates a comment in a Notion page or discussion thread.
    Either page_id or discussion_id must be provided, but not both.
    """
    client = NotionClient()
    
    if not (bool(page_id) ^ bool(discussion_id)):
        raise ValueError("Either page_id or discussion_id must be provided, but not both")
        
    data = {
        "rich_text": rich_text
    }
    
    if page_id:
        data["parent"] = {"page_id": page_id}
    if discussion_id:
        data["discussion_id"] = discussion_id
        
    return client._make_request("POST", "comments", data)

@weave.op(name="notion-get_comments")
def get_comments(*, 
                block_id: str,
                start_cursor: Optional[str] = None,
                page_size: Optional[int] = None) -> Dict:
    """
    Retrieves comments from a block.
    """
    client = NotionClient()
    
    params = {"block_id": block_id}
    if start_cursor:
        params["start_cursor"] = start_cursor
    if page_size:
        params["page_size"] = page_size
        
    return client._make_request("GET", "comments", params) 

@weave.op(name="notion-create_page")
def create_page(*,
                parent: Dict,
                properties: Dict,
                children: Optional[List[Dict]] = None,
                icon: Optional[Dict] = None,
                cover: Optional[Dict] = None) -> Dict:
    """
    Creates a new page in Notion.
    Parent must specify either a parent page ID or database ID.
    Properties depend on the parent type - only title for pages, matching properties for databases.
    """
    client = NotionClient()
    
    data = {
        "parent": {parent["type"]: parent["id"]},
        "properties": properties
    }
    
    if children:
        data["children"] = children
    if icon:
        data["icon"] = icon
    if cover:
        data["cover"] = cover
        
    return client._make_request("POST", "pages", data) 

@weave.op(name="notion-update_block")
def update_block(*, block_id: str, block_type: str, content: Dict) -> Dict:
    """
    Updates a block's content in Notion.
    The content structure must match the block type according to Notion's API.
    Note: This cannot update children blocks or change block type.
    
    Example usage:
    update_block(
        block_id="block_id_here",
        block_type="paragraph",
        content={
            "rich_text": [{
                "text": {
                    "content": "New text content"
                }
            }]
        }
    )
    """
    if not content:
        raise ValueError("Content parameter is required and cannot be empty")
        
    client = NotionClient()
    
    # The content should be directly under the block_type key, not nested
    data = {
        block_type: content.get(block_type, content)
    }
        
    return client._make_request("PATCH", f"blocks/{block_id}", data) 