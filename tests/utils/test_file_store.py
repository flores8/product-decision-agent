import pytest
import os
from pathlib import Path
import tempfile
import shutil
from typing import AsyncGenerator
from tyler.storage.file_store import (
    FileStore, 
    FileStoreError,
    FileNotFoundError,
    StorageFullError,
    UnsupportedFileTypeError,
    FileTooLargeError
)

@pytest.fixture
async def temp_store() -> AsyncGenerator[FileStore, None]:
    """Create a temporary FileStore for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        store = FileStore(base_path=temp_dir)
        yield store

@pytest.mark.asyncio
async def test_save_and_get(temp_store: FileStore):
    """Test basic file save and retrieval."""
    content = b'Hello, World!'
    filename = 'test.txt'
    
    # Test saving
    result = await temp_store.save(content=content, filename=filename)
    assert result['id'] is not None
    assert result['storage_path'] is not None
    assert result['filename'] == filename
    assert result['mime_type'] == 'text/plain'
    assert result['metadata']['size'] == len(content)
    
    # Test retrieval
    retrieved = await temp_store.get(result['id'], result['storage_path'])
    assert retrieved == content
    
    # Verify file exists on disk
    full_path = temp_store.base_path / result['storage_path']
    assert full_path.exists()
    assert full_path.stat().st_size == len(content)

@pytest.mark.asyncio
async def test_file_not_found(temp_store: FileStore):
    """Test handling of non-existent files."""
    with pytest.raises(FileNotFoundError):
        await temp_store.get('nonexistent-id')

@pytest.mark.asyncio
async def test_file_size_limit(temp_store: FileStore):
    """Test file size limit enforcement."""
    # Set a small file size limit
    temp_store.max_file_size = 10
    content = b'This content is too large'
    
    with pytest.raises(FileTooLargeError):
        await temp_store.save(content=content, filename='large.txt')

@pytest.mark.asyncio
async def test_mime_type_validation(temp_store: FileStore):
    """Test MIME type validation."""
    # Set allowed MIME types to only text/plain
    temp_store.allowed_mime_types = {'text/plain'}
    
    # Test allowed MIME type
    await temp_store.save(content=b'text content', filename='test.txt')
    
    # Test disallowed MIME type
    with pytest.raises(UnsupportedFileTypeError):
        await temp_store.save(content=b'PNG content', filename='test.png')

@pytest.mark.asyncio
async def test_delete(temp_store: FileStore):
    """Test file deletion."""
    content = b'Delete me'
    result = await temp_store.save(content=content, filename='delete.txt')
    
    # Verify file exists
    file_path = temp_store.base_path / result['storage_path']
    assert file_path.exists()
    
    # Delete file using storage path
    await temp_store.delete(result['id'], result['storage_path'])
    
    # Verify file is gone
    assert not file_path.exists()
    with pytest.raises(FileNotFoundError):
        await temp_store.get(result['id'], result['storage_path'])

@pytest.mark.asyncio
async def test_storage_metrics(temp_store: FileStore):
    """Test storage size and file count metrics."""
    content1 = b'File 1'
    content2 = b'File 2'
    
    # Save two files
    result1 = await temp_store.save(content=content1, filename='file1.txt')
    result2 = await temp_store.save(content=content2, filename='file2.txt')
    
    # Check metrics
    size = await temp_store.get_storage_size()
    count = await temp_store.get_file_count()
    
    # Only count actual files, not directories
    expected_size = len(content1) + len(content2)
    assert size == expected_size
    
    # Count should include both files and their parent directories
    # Each file is stored in a sharded directory structure: base_dir/xx/filename
    # So for each file we have: the file itself and its parent directory
    expected_count = 4  # 2 files + 2 parent directories
    assert count == expected_count

@pytest.mark.asyncio
async def test_batch_operations(temp_store: FileStore):
    """Test batch save and delete operations."""
    files = [
        (b'Content 1', 'file1.txt', 'text/plain'),
        (b'Content 2', 'file2.txt', 'text/plain')
    ]
    
    # Test batch save
    results = await temp_store.batch_save(files)
    assert len(results) == 2
    file_ids = [r['id'] for r in results]
    
    # Verify files exist
    for result in results:
        content = await temp_store.get(result['id'], result['storage_path'])
        assert content is not None
    
    # Test batch delete
    for result in results:
        await temp_store.delete(result['id'], result['storage_path'])
    
    # Verify files are gone
    for result in results:
        with pytest.raises(FileNotFoundError):
            await temp_store.get(result['id'], result['storage_path'])

@pytest.mark.asyncio
async def test_storage_limit(temp_store: FileStore):
    """Test storage capacity limit."""
    # Set a small storage limit
    temp_store.max_storage_size = 10
    content = b'This will exceed storage limit'
    
    with pytest.raises(StorageFullError):
        await temp_store.save(content=content, filename='big.txt')

@pytest.mark.asyncio
async def test_health_check(temp_store: FileStore):
    """Test health check functionality."""
    health = await temp_store.check_health()
    
    assert 'healthy' in health
    assert 'total_size' in health
    assert 'file_count' in health
    assert 'errors' in health
    assert health['healthy'] is True
    assert isinstance(health['total_size'], int)
    assert isinstance(health['file_count'], int)
    assert isinstance(health['errors'], list) 