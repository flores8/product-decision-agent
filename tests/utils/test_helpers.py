import pytest
import os
from unittest.mock import patch, MagicMock
from utils.helpers import get_all_tools

def test_get_all_tools_empty_directory():
    """Test when tools directory is empty or doesn't exist"""
    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir:
        
        # Simulate directory doesn't exist
        mock_exists.return_value = False
        assert get_all_tools() == []
        
        # Simulate empty directory
        mock_exists.return_value = True
        mock_listdir.return_value = []
        assert get_all_tools() == []

def test_get_all_tools_with_list_tools():
    """Test loading tools defined as lists"""
    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir, \
         patch('importlib.import_module') as mock_import:
        
        mock_exists.return_value = True
        mock_listdir.return_value = ['test_tools.py']
        
        # Create mock module with list tools
        mock_module = MagicMock()
        mock_module.TEST_TOOLS = ['tool1', 'tool2']
        mock_import.return_value = mock_module
        
        tools = get_all_tools()
        assert tools == ['tool1', 'tool2']

def test_get_all_tools_with_dict_tools():
    """Test loading tools defined as dictionaries"""
    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir, \
         patch('importlib.import_module') as mock_import:
        
        mock_exists.return_value = True
        mock_listdir.return_value = ['test_tools.py']
        
        # Create mock module with dict tools
        mock_module = MagicMock()
        mock_module.TEST_TOOLS = {
            'tool1': 'tool1_impl',
            'tool2': 'tool2_impl'
        }
        mock_import.return_value = mock_module
        
        tools = get_all_tools()
        assert tools == ['tool1_impl', 'tool2_impl']

def test_get_all_tools_multiple_files():
    """Test loading tools from multiple files"""
    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir, \
         patch('importlib.import_module') as mock_import:
        
        mock_exists.return_value = True
        mock_listdir.return_value = ['tools1.py', 'tools2.py']
        
        # Create mock modules
        mock_module1 = MagicMock()
        mock_module1.TOOLS1_TOOLS = ['tool1', 'tool2']
        
        mock_module2 = MagicMock()
        mock_module2.TOOLS2_TOOLS = {'tool3': 'tool3_impl'}
        
        mock_import.side_effect = [mock_module1, mock_module2]
        
        tools = get_all_tools()
        assert tools == ['tool1', 'tool2', 'tool3_impl']

def test_get_all_tools_handles_errors():
    """Test error handling when loading tools"""
    with patch('os.path.exists') as mock_exists, \
         patch('os.listdir') as mock_listdir, \
         patch('importlib.import_module') as mock_import:
        
        mock_exists.return_value = True
        mock_listdir.return_value = ['broken_tools.py']
        
        # Simulate import error
        mock_import.side_effect = ImportError("Module not found")
        
        tools = get_all_tools()
        assert tools == [] 