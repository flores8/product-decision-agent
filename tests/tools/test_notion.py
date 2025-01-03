import pytest
from unittest.mock import patch, MagicMock
from tools.notion import NotionClient, search, get_page, get_page_content
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
    ],
    "next_cursor": None,
    "has_more": False
}

@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Clear environment variables before each test"""
    monkeypatch.delenv("NOTION_TOKEN", raising=False)

@pytest.fixture
def mock_env_token(monkeypatch):
    """Fixture to mock NOTION_TOKEN environment variable"""
    monkeypatch.setenv("NOTION_TOKEN", "mock-token")

def test_notion_client_init_missing_token():
    """Test NotionClient initialization with missing token"""
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