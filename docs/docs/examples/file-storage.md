# File Storage Example

This example demonstrates how to use Tyler's file storage capabilities to save and retrieve files.

## Configuration

First, set up the file storage configuration:

```typescript
import { Agent } from 'tyler';

const agent = new Agent({
  storage: {
    type: 'file',
    config: {
      directory: './storage', // Directory where files will be stored
      maxSize: '100mb',      // Maximum file size
    }
  }
});
```

## Saving Files

```typescript
// Save a file
const fileContent = Buffer.from('Hello, World!');
await agent.storage.saveFile('example.txt', fileContent);

// Save with metadata
await agent.storage.saveFile('data.json', jsonContent, {
  type: 'application/json',
  created: new Date()
});
```

## Retrieving Files

```typescript
// Get file content
const content = await agent.storage.getFile('example.txt');

// Get file with metadata
const { content, metadata } = await agent.storage.getFileWithMetadata('data.json');
```

## Listing Files

```typescript
// List all files
const files = await agent.storage.listFiles();

// List files with pattern
const jsonFiles = await agent.storage.listFiles('*.json');
```

## Deleting Files

```typescript
// Delete a file
await agent.storage.deleteFile('example.txt');

// Delete multiple files
await agent.storage.deleteFiles(['data.json', 'temp.txt']);
```

## Complete Example

Here's a complete example showing various file operations:

```typescript
import { Agent } from 'tyler';

async function main() {
  const agent = new Agent({
    storage: {
      type: 'file',
      config: {
        directory: './storage',
        maxSize: '100mb'
      }
    }
  });

  // Save some files
  await agent.storage.saveFile('doc1.txt', Buffer.from('Document 1'));
  await agent.storage.saveFile('doc2.txt', Buffer.from('Document 2'));

  // List all text files
  const textFiles = await agent.storage.listFiles('*.txt');
  console.log('Text files:', textFiles);

  // Read file contents
  for (const file of textFiles) {
    const content = await agent.storage.getFile(file);
    console.log(`${file} contents:`, content.toString());
  }

  // Clean up
  await agent.storage.deleteFiles(textFiles);
}

main().catch(console.error);
```

## Error Handling

```typescript
try {
  await agent.storage.getFile('nonexistent.txt');
} catch (error) {
  if (error.code === 'FILE_NOT_FOUND') {
    console.error('File does not exist');
  } else {
    console.error('Other error:', error);
  }
}
``` 