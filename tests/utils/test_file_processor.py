import pytest
import io
import base64
from unittest.mock import Mock, patch, MagicMock
from tyler.utils.file_processor import FileProcessor, process_file
from PyPDF2 import PdfReader
from PIL import Image
from PyPDF2.errors import PdfReadError

@pytest.fixture
def file_processor():
    return FileProcessor()

@pytest.fixture
def sample_pdf_content():
    # Create a simple PDF-like bytes object for testing
    return b"%PDF-1.4\nsome content"

@pytest.fixture
def mock_openai_response():
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="Extracted text from image"))]
    return mock_response

@pytest.fixture
def mock_pdf_reader():
    """Create a properly mocked PDF reader"""
    mock_reader = Mock(spec=PdfReader)
    mock_page = Mock()
    mock_page.extract_text.return_value = "Extracted PDF text"
    mock_reader.pages = [mock_page]
    return mock_reader

def test_format_message_content_text_only(file_processor):
    """Test formatting message content with text only"""
    result = file_processor._format_message_content("test content")
    assert result == "test content"

def test_format_message_content_with_image(file_processor):
    """Test formatting message content with both text and image"""
    image_data = {
        "mime_type": "image/png",
        "content": "base64content"
    }
    result = file_processor._format_message_content("test content", image_data)
    assert isinstance(result, str)
    parsed = eval(result)  # Safe since we control the input
    assert len(parsed) == 2
    assert parsed[0]["type"] == "text"
    assert parsed[1]["type"] == "image_url"

@patch('magic.from_buffer')
def test_process_file_unsupported_type(mock_magic, file_processor):
    """Test processing an unsupported file type"""
    mock_magic.return_value = "application/unsupported"
    result = file_processor.process_file(b"content", "test.doc")
    assert "error" in result
    assert "Unsupported file type" in result["error"]

@patch('magic.from_buffer')
@patch('tyler.utils.file_processor.PdfReader')
def test_process_file_pdf_extension_override(mock_pdf_reader_cls, mock_magic, file_processor, mock_pdf_reader):
    """Test processing a file with .pdf extension but different mime type"""
    mock_magic.return_value = "text/plain"
    mock_pdf_reader_cls.return_value = mock_pdf_reader
    result = file_processor.process_file(b"content", "test.pdf")
    assert result["text"] == "Extracted PDF text"
    assert result["type"] == "pdf"

@patch('tyler.utils.file_processor.PdfReader')
def test_process_pdf_text_extraction(mock_pdf_reader_cls, file_processor, mock_pdf_reader):
    """Test PDF processing with successful text extraction"""
    mock_pdf_reader_cls.return_value = mock_pdf_reader
    
    result = file_processor._process_pdf(b"pdf content")
    
    assert result["text"] == "Extracted PDF text"
    assert result["type"] == "pdf"
    assert result["processing_method"] == "text"
    assert result["empty_pages"] == []

@patch('tyler.utils.file_processor.PdfReader')
def test_process_pdf_empty_pages(mock_pdf_reader_cls, file_processor):
    """Test PDF processing with empty pages"""
    mock_reader = Mock(spec=PdfReader)
    mock_page = Mock()
    mock_page.extract_text.return_value = ""
    mock_reader.pages = [mock_page]
    mock_pdf_reader_cls.return_value = mock_reader
    
    with patch.object(file_processor, '_process_pdf_with_vision') as mock_vision:
        mock_vision.return_value = {"text": "Vision extracted text"}
        result = file_processor._process_pdf(b"pdf content")
        assert mock_vision.called
        assert result == {"text": "Vision extracted text"}

@patch('pdf2image.convert_from_bytes')
def test_process_pdf_with_vision_error(mock_convert, file_processor):
    """Test error handling in Vision API processing"""
    mock_convert.side_effect = Exception("Conversion failed")
    
    result = file_processor._process_pdf_with_vision(b"pdf content")
    
    assert "error" in result
    assert "Failed to process PDF with Vision API" in result["error"]

def test_process_file_function():
    """Test the standalone process_file function"""
    with patch.object(FileProcessor, 'process_file') as mock_process:
        mock_process.return_value = {"text": "processed content"}
        result = process_file(b"content", "test.pdf")
        assert mock_process.called
        assert result == {"text": "processed content"}

@patch('tyler.utils.file_processor.PdfReader')
def test_process_pdf_page_extraction_error(mock_pdf_reader_cls, file_processor):
    """Test handling of page extraction errors"""
    mock_reader = Mock(spec=PdfReader)
    mock_page = Mock()
    mock_page.extract_text.side_effect = Exception("Page extraction failed")
    mock_reader.pages = [mock_page]
    mock_pdf_reader_cls.return_value = mock_reader
    
    with patch.object(file_processor, '_process_pdf_with_vision') as mock_vision:
        mock_vision.return_value = {"text": "Vision extracted text"}
        result = file_processor._process_pdf(b"pdf content")
        assert mock_vision.called
        assert result == {"text": "Vision extracted text"}

@pytest.mark.parametrize("mime_type,filename,expected_processor", [
    ("application/pdf", "test.pdf", "_process_pdf"),
    ("text/plain", "test.pdf", "_process_pdf"),  # PDF extension override
])
@patch('magic.from_buffer')
@patch('tyler.utils.file_processor.PdfReader')
def test_process_file_routing(mock_pdf_reader_cls, mock_magic, file_processor, mime_type, filename, expected_processor, mock_pdf_reader):
    """Test correct routing of different file types to their processors"""
    mock_magic.return_value = mime_type
    mock_pdf_reader_cls.return_value = mock_pdf_reader
    
    result = file_processor.process_file(b"content", filename)
    assert result["text"] == "Extracted PDF text"
    assert result["type"] == "pdf" 