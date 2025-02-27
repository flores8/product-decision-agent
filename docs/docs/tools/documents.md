# Documents Tools

The documents module provides specialized tools for processing and analyzing various document formats including PDFs, CSV files, and JSON documents.

## Available Tools

### extract-pdf-text

Extract text content from PDF files with page-level control.

#### Parameters

- `file_url` (string, required)
  - Full path to the PDF file
  - Must be a valid local file path

- `pages` (array of integers, optional)
  - List of specific pages to extract (1-based)
  - If not provided, extracts all pages

#### Returns

A dictionary containing:
- `success`: Boolean indicating success
- `pages`: Array of page objects containing:
  - `page`: Page number
  - `content`: Extracted text
- `total_pages`: Total number of pages in PDF
- `file_url`: Original file path
- `error`: Error message if failed

### parse-csv

Parse and analyze CSV file content with statistics and preview.

#### Parameters

- `file_url` (string, required)
  - Full path to the CSV file
  - Must be a valid local file path

- `preview_rows` (integer, optional)
  - Number of rows to include in preview
  - Default: 5

- `delimiter` (string, optional)
  - CSV delimiter character
  - Default: ","

#### Returns

A dictionary containing:
- `success`: Boolean indicating success
- `statistics`: Dictionary containing:
  - `total_rows`: Number of rows
  - `total_columns`: Number of columns
  - `columns`: List of column names
  - `column_types`: Dictionary of column data types
- `preview`: Array of preview rows
- `file_url`: Original file path
- `error`: Error message if failed

### parse-json

Parse and extract data from JSON files with path-based extraction.

#### Parameters

- `file_url` (string, required)
  - Full path to the JSON file
  - Must be a valid local file path

- `path` (string, optional)
  - JSON path to extract specific data
  - Example: "data.items[0].name"

#### Returns

A dictionary containing:
- `success`: Boolean indicating success
- `data`: Parsed JSON data or extracted value
- `file_url`: Original file path
- `error`: Error message if failed

## Example Usage

```python
from tyler.models import Agent, Thread, Message

# Create an agent with document tools
agent = Agent(
    model_name="gpt-4o",
    purpose="To help with document processing",
    tools=["documents"]
)

# Create a thread to extract PDF text
thread = Thread()
message = Message(
    role="user",
    content="Extract text from pages 1-3 of document.pdf"
)
thread.add_message(message)

# Process the thread - agent will use extract-pdf-text tool
processed_thread, new_messages = await agent.go(thread)

# Example of CSV parsing
csv_thread = Thread()
message = Message(
    role="user",
    content="Analyze the contents of data.csv and show me a preview"
)
csv_thread.add_message(message)

# Process the thread - agent will use parse-csv tool
processed_csv, new_messages = await agent.go(csv_thread)
```

## Best Practices

1. **PDF Processing**
   - Extract specific pages when possible
   - Handle large documents in chunks
   - Consider text encoding
   - Preserve document structure

2. **CSV Handling**
   - Verify delimiter settings
   - Handle header rows properly
   - Check data types
   - Validate data consistency

3. **JSON Processing**
   - Validate JSON structure
   - Use specific paths for large files
   - Handle nested data carefully
   - Consider memory usage

4. **Error Management**
   - Validate input files
   - Handle parsing errors
   - Check data integrity
   - Monitor resource usage

## Common Use Cases

1. **Data Extraction**
   - PDF text extraction
   - CSV data analysis
   - JSON data parsing
   - Structured data extraction

2. **Document Analysis**
   - Content validation
   - Data profiling
   - Format verification
   - Structure analysis

3. **Data Processing**
   - Format conversion
   - Data transformation
   - Content extraction
   - Statistical analysis

## Limitations

1. **PDF Processing**
   - OCR not included
   - Complex layouts may affect accuracy
   - Large file handling
   - Font dependency

2. **CSV Processing**
   - Memory constraints for large files
   - Encoding limitations
   - Type inference accuracy
   - Special character handling

3. **JSON Processing**
   - Memory usage for large files
   - Deep nesting limitations
   - Path complexity
   - Schema validation

## Error Handling

Common errors and solutions:

1. **File Issues**
   - Validate file existence
   - Check file permissions
   - Verify file format
   - Handle corrupt files

2. **Processing Errors**
   - Handle malformed data
   - Manage memory usage
   - Process timeout handling
   - Data validation errors

3. **Resource Management**
   - Monitor memory usage
   - Handle large files
   - Manage concurrent processing
   - Control processing time 