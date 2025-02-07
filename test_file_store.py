from tyler.storage import FileStore
import asyncio
from pathlib import Path

async def test_save():
    store = FileStore()
    print(f'Storage location: {store.base_path}')
    
    test_content = b'Hello, World!'
    result = await store.save(content=test_content, filename='test.txt')
    print(f'\nFile saved:')
    print(f'- ID: {result["id"]}')
    print(f'- Storage path: {result["storage_path"]}')
    print(f'- Full path: {store.base_path / result["storage_path"]}')
    
    # Verify file exists and content matches
    content = await store.get(result['id'])
    print(f'\nFile verification:')
    print(f'- Content matches: {content == test_content}')
    print(f'- Content: {content.decode()}')
    
    # Check if file exists on disk
    full_path = store.base_path / result['storage_path']
    print(f'\nFile system check:')
    print(f'- File exists: {full_path.exists()}')
    if full_path.exists():
        print(f'- File size: {full_path.stat().st_size} bytes')
        print(f'- File permissions: {oct(full_path.stat().st_mode)[-3:]}')

if __name__ == '__main__':
    asyncio.run(test_save()) 