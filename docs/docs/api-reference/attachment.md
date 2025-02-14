# Attachment

The `Attachment` class represents a file or data attachment that can be included with messages in Tyler.

## Properties

- `type` (string): The type of attachment (e.g., 'file', 'image', 'data')
- `content` (any): The content of the attachment
- `metadata` (object): Additional metadata about the attachment

## Methods

### constructor(type: string, content: any, metadata?: object)

Creates a new Attachment instance.

```typescript
const attachment = new Attachment('file', fileContent, { filename: 'example.txt' });
```

### getContent()

Returns the content of the attachment.

```typescript
const content = attachment.getContent();
```

### getMetadata()

Returns the metadata associated with the attachment.

```typescript
const metadata = attachment.getMetadata();
```

## Usage Example

```typescript
import { Attachment } from 'tyler';

// Create a file attachment
const fileAttachment = new Attachment('file', fileBuffer, {
  filename: 'document.pdf',
  mimeType: 'application/pdf'
});

// Create a data attachment
const dataAttachment = new Attachment('data', {
  key: 'value',
  numbers: [1, 2, 3]
});
``` 