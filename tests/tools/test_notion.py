import pytest
from unittest.mock import patch, MagicMock
from tools.notion import NotionClient, search, get_page, get_page_content, create_comment, get_comments, create_page, update_block
import requests

# Mock API responses
MOCK_SEARCH_RESPONSE = {
    "results": [
        {
            "object": "page",
            "id": "page1",
            "properties": {"title": "Test Page"}
        }
    ],
    "next_cursor": "cursor1",
    "has_more": False
}

MOCK_PAGE_RESPONSE = {
    "object": "page",
    "id": "page1",
    "properties": {
        "title": {"type": "title", "title": [{"text": {"content": "Test Page"}}]}
    }
}

MOCK_PAGE_CONTENT_RESPONSE = {
    "object": "list",
    "results": [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"text": [{"text": {"content": "Test content"}}]}
        }
    ]
}

MOCK_COMMENT_RESPONSE = {
    "object": "comment",
    "id": "comment1",
    "parent": {"type": "page_id", "page_id": "page1"},
    "rich_text": [{"text": {"content": "Test comment"}}]
}

MOCK_COMMENTS_LIST_RESPONSE = {
    "object": "list",
    "results": [MOCK_COMMENT_RESPONSE],
    "next_cursor": None,
    "has_more": False
}

MOCK_CREATE_PAGE_RESPONSE = {
    "object": "page",
    "id": "new_page1",
    "parent": {"type": "page_id", "page_id": "parent1"},
    "properties": {
        "title": {"type": "title", "title": [{"text": {"content": "New Test Page"}}]}
    }
}

MOCK_UPDATE_BLOCK_RESPONSE = {
    "object": "block",
    "id": "block1",
    "type": "paragraph",
    "paragraph": {
        "rich_text": [{"text": {"content": "Updated content"}}]
    }
}

@pytest.fixture(autouse=True)
def mock_requests():
    """Mock all requests to prevent any real API calls"""
    with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_SEARCH_RESPONSE
        mock_get.return_value = mock_response
        mock_post.return_value = mock_response
        yield mock_get, mock_post

@pytest.fixture
def mock_env_token(monkeypatch):
    """Fixture to mock NOTION_TOKEN environment variable"""
    monkeypatch.setenv("NOTION_TOKEN", "mock-token")

def test_notion_client_init_missing_token(monkeypatch):
    """Test NotionClient initialization with missing token"""
    # Clear both environment variable and streamlit secrets
    monkeypatch.delenv("NOTION_TOKEN", raising=False)
    with patch('streamlit.secrets', new={}):
        with pytest.raises(ValueError, match="NOTION_TOKEN environment variable is required"):
            NotionClient()

def test_notion_client_init(mock_env_token):
    """Test NotionClient initialization with token"""
    client = NotionClient()
    assert client.token == "mock-token"
    assert client.headers["Authorization"] == "Bearer mock-token"
    assert client.headers["Notion-Version"] == "2022-06-28"

@patch('requests.post')
def test_search_function(mock_post, mock_env_token):
    """Test search function"""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_SEARCH_RESPONSE
    mock_post.return_value = mock_response

    result = search(
        query="test",
        filter={"property": "object", "value": "page"},
        start_cursor="cursor1",
        page_size=10
    )

    mock_post.assert_called_once()
    assert result == MOCK_SEARCH_RESPONSE
    
    # Verify the request was made with correct parameters
    call_kwargs = mock_post.call_args[1]
    assert "json" in call_kwargs
    assert call_kwargs["json"]["query"] == "test"
    assert call_kwargs["json"]["filter"] == {"property": "object", "value": "page"}
    assert call_kwargs["json"]["start_cursor"] == "cursor1"
    assert call_kwargs["json"]["page_size"] == 10

@patch('requests.get')
def test_get_page_function(mock_get, mock_env_token):
    """Test get_page function"""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_PAGE_RESPONSE
    mock_get.return_value = mock_response

    result = get_page(page_id="page1")

    mock_get.assert_called_once()
    assert result == MOCK_PAGE_RESPONSE

@patch('requests.get')
def test_get_page_content_function(mock_get, mock_env_token):
    """Test get_page_content function"""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_PAGE_CONTENT_RESPONSE
    mock_get.return_value = mock_response

    result = get_page_content(
        page_id="page1",
        start_cursor="cursor1",
        page_size=10
    )

    mock_get.assert_called_once()
    assert result == MOCK_PAGE_CONTENT_RESPONSE

@patch('requests.post')
def test_notion_api_error_handling(mock_post, mock_env_token):
    """Test error handling for API requests"""
    # Simulate API error
    mock_response = MagicMock()
    mock_error = requests.exceptions.RequestException("API Error")
    mock_error.response = MagicMock()
    mock_error.response.json.return_value = {"error": "Invalid request"}
    mock_post.side_effect = mock_error

    with pytest.raises(Exception, match="Notion API request failed: API Error"):
        search(query="test")

def test_search_with_minimal_params(mock_env_token):
    """Test search function with minimal parameters"""
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_SEARCH_RESPONSE
        mock_post.return_value = mock_response

        result = search()  # No parameters provided

        mock_post.assert_called_once()
        assert result == MOCK_SEARCH_RESPONSE
        
        # Verify empty request body
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"] == {} 

@patch('requests.post')
def test_create_comment_with_page_id(mock_post, mock_env_token):
    """Test create_comment function with page_id"""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_COMMENT_RESPONSE
    mock_post.return_value = mock_response

    rich_text = [{"text": {"content": "Test comment"}}]
    result = create_comment(page_id="page1", rich_text=rich_text)

    mock_post.assert_called_once()
    assert result == MOCK_COMMENT_RESPONSE
    
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"]["parent"] == {"page_id": "page1"}
    assert call_kwargs["json"]["rich_text"] == rich_text

@patch('requests.post')
def test_create_comment_with_discussion_id(mock_post, mock_env_token):
    """Test create_comment function with discussion_id"""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_COMMENT_RESPONSE
    mock_post.return_value = mock_response

    rich_text = [{"text": {"content": "Test comment"}}]
    result = create_comment(discussion_id="discussion1", rich_text=rich_text)

    mock_post.assert_called_once()
    assert result == MOCK_COMMENT_RESPONSE
    
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"]["discussion_id"] == "discussion1"
    assert call_kwargs["json"]["rich_text"] == rich_text

def test_create_comment_invalid_params(mock_env_token):
    """Test create_comment with invalid parameters"""
    rich_text = [{"text": {"content": "Test comment"}}]
    
    # Test with both page_id and discussion_id
    with pytest.raises(ValueError, match="Either page_id or discussion_id must be provided, but not both"):
        create_comment(page_id="page1", discussion_id="discussion1", rich_text=rich_text)
    
    # Test with neither page_id nor discussion_id
    with pytest.raises(ValueError, match="Either page_id or discussion_id must be provided, but not both"):
        create_comment(rich_text=rich_text)

@patch('requests.get')
def test_get_comments(mock_get, mock_env_token):
    """Test get_comments function with all parameters"""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_COMMENTS_LIST_RESPONSE
    mock_get.return_value = mock_response

    result = get_comments(
        block_id="block1",
        start_cursor="cursor1",
        page_size=10
    )

    mock_get.assert_called_once()
    assert result == MOCK_COMMENTS_LIST_RESPONSE
    
    # Verify the request parameters
    call_kwargs = mock_get.call_args[1]
    assert "params" in call_kwargs
    assert call_kwargs["params"]["block_id"] == "block1"
    assert call_kwargs["params"]["start_cursor"] == "cursor1"
    assert call_kwargs["params"]["page_size"] == 10

@patch('requests.get')
def test_get_comments_minimal_params(mock_get, mock_env_token):
    """Test get_comments function with only required parameters"""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_COMMENTS_LIST_RESPONSE
    mock_get.return_value = mock_response

    result = get_comments(block_id="block1")

    mock_get.assert_called_once()
    assert result == MOCK_COMMENTS_LIST_RESPONSE
    
    # Verify only required parameters are sent
    call_kwargs = mock_get.call_args[1]
    assert "params" in call_kwargs
    assert call_kwargs["params"] == {"block_id": "block1"}
    assert "start_cursor" not in call_kwargs["params"]
    assert "page_size" not in call_kwargs["params"]

@patch('requests.post')
def test_create_page(mock_post, mock_env_token):
    """Test create_page function"""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_CREATE_PAGE_RESPONSE
    mock_post.return_value = mock_response

    parent = {"type": "page_id", "id": "parent1"}
    properties = {"title": {"title": [{"text": {"content": "New Test Page"}}]}}
    children = [{"type": "paragraph", "paragraph": {"text": [{"text": {"content": "Test content"}}]}}]
    icon = {"type": "emoji", "emoji": "📝"}
    cover = {"type": "external", "external": {"url": "https://example.com/image.jpg"}}

    result = create_page(
        parent=parent,
        properties=properties,
        children=children,
        icon=icon,
        cover=cover
    )

    mock_post.assert_called_once()
    assert result == MOCK_CREATE_PAGE_RESPONSE
    
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"]["parent"] == {"page_id": "parent1"}
    assert call_kwargs["json"]["properties"] == properties
    assert call_kwargs["json"]["children"] == children
    assert call_kwargs["json"]["icon"] == icon
    assert call_kwargs["json"]["cover"] == cover

@patch('requests.patch')
def test_update_block(mock_patch, mock_env_token):
    """Test update_block function"""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_UPDATE_BLOCK_RESPONSE
    mock_patch.return_value = mock_response

    block_type = "paragraph"
    content = {
        "rich_text": [{"text": {"content": "Updated content"}}]
    }

    result = update_block(
        block_id="block1",
        block_type=block_type,
        content=content
    )

    mock_patch.assert_called_once()
    assert result == MOCK_UPDATE_BLOCK_RESPONSE
    
    call_kwargs = mock_patch.call_args[1]
    assert call_kwargs["json"] == {block_type: content}

def test_update_block_empty_content(mock_env_token):
    """Test update_block with empty content"""
    with pytest.raises(ValueError, match="Content parameter is required and cannot be empty"):
        update_block(block_id="block1", block_type="paragraph", content={}) 