import pytest
from tyler.tools.image import generate_image
import base64
from unittest.mock import patch, AsyncMock, MagicMock

@pytest.fixture
def mock_image_response():
    """Mock response that matches litellm's image_generation format"""
    return {
        "created": 1234567890,
        "data": [{
            "url": "https://example.com/image.png",
            "revised_prompt": "A beautiful test image",
            "model": "dall-e-3"
        }]
    }

@pytest.fixture
def mock_image_bytes():
    return b"fake image data"

@pytest.mark.asyncio
async def test_generate_image_success(mock_image_response, mock_image_bytes):
    """Test successful image generation with new tuple return format"""
    # Create a mock for litellm.image_generation
    mock_generation = MagicMock(return_value=mock_image_response)
    
    with patch('tyler.tools.image.image_generation', mock_generation), \
         patch('httpx.AsyncClient') as mock_client:
        # Mock the HTTP response for image download
        mock_response = AsyncMock()
        mock_response.content = mock_image_bytes
        mock_response.raise_for_status = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await generate_image(prompt="test image")
        
        # Verify litellm was called with correct parameters
        mock_generation.assert_called_once_with(
            prompt="test image",
            model="dall-e-3",
            n=1,
            size="1024x1024",
            quality="standard",
            style="vivid",
            response_format="url"
        )
        
        # Check tuple structure
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        # Check content dict
        content, files = result
        assert isinstance(content, dict)
        assert content["success"] is True
        assert content["description"] == mock_image_response["data"][0]["revised_prompt"]
        assert "details" in content
        assert isinstance(content["details"], dict)
        assert content["details"]["filename"] == f"generated_image_{mock_image_response['created']}.png"
        
        # Check files list
        assert isinstance(files, list)
        assert len(files) == 1
        file_info = files[0]
        assert file_info["content"] == base64.b64encode(mock_image_bytes).decode('utf-8')
        assert file_info["filename"] == f"generated_image_{mock_image_response['created']}.png"
        assert file_info["mime_type"] == "image/png"
        assert file_info["description"] == mock_image_response["data"][0]["revised_prompt"]

@pytest.mark.asyncio
async def test_generate_image_error():
    """Test error handling with new tuple return format"""
    # Test with invalid size to trigger error
    result = await generate_image(prompt="test", size="invalid")
    
    # Check tuple structure
    assert isinstance(result, tuple)
    assert len(result) == 2
    
    # Check error content
    content, files = result
    assert isinstance(content, dict)
    assert content["success"] is False
    assert "error" in content
    assert "Size invalid not supported" in content["error"]
    
    # Check files is empty list for error case
    assert isinstance(files, list)
    assert len(files) == 0

@pytest.mark.asyncio
async def test_generate_image_parameters(mock_image_response, mock_image_bytes):
    """Test image generation with different parameters"""
    # Create a mock for litellm.image_generation
    mock_generation = MagicMock(return_value=mock_image_response)
    
    with patch('tyler.tools.image.image_generation', mock_generation), \
         patch('httpx.AsyncClient') as mock_client:
        # Mock the HTTP response for image download
        mock_response = AsyncMock()
        mock_response.content = mock_image_bytes
        mock_response.raise_for_status = AsyncMock()
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await generate_image(
            prompt="test image",
            size="1024x1024",
            quality="hd",
            style="natural"
        )
        
        # Verify litellm was called with correct parameters
        mock_generation.assert_called_once_with(
            prompt="test image",
            model="dall-e-3",
            n=1,
            size="1024x1024",
            quality="hd",
            style="natural",
            response_format="url"
        )
        
        # Check content details
        content, files = result
        assert content["success"] is True
        assert content["details"]["size"] == "1024x1024"
        assert content["details"]["quality"] == "hd"
        assert content["details"]["style"] == "natural"
        
        # Check file was generated
        assert len(files) == 1
        assert files[0]["mime_type"] == "image/png" 