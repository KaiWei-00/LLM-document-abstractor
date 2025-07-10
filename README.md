# Document Extraction Service API

A powerful microservice for extracting structured information from documents using AI.

## Overview

This API service uses LangGraph and OpenAI models to automatically extract structured data from various document types (PDF, Excel, Word). It provides a simple REST API that allows you to upload documents and receive extracted information based on your specified schema.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Error Handling](#error-handling)

## Features

- Extract structured information from PDF, Excel, and Word documents
- Schema-based extraction (define exactly what fields you want to extract)
- Automatic document type detection
- JSON output for easy integration
- Stores extraction results for future reference

## Installation

### Prerequisites

- Python 3.10+
- OpenAI API key

### Setup

1. Clone this repository:
```bash
git clone <repository-url>
cd document-extraction-service
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo  # or any other compatible model
```

5. Start the server:
```bash
python main.py
# Or use uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Reference

### Endpoints

#### 1. Extract Document Information

```
POST /extract
```

Extracts structured information from a document based on a provided schema.

**Request Format:**
- Content-Type: `multipart/form-data`
- Parameters:
  - `file`: The document file (PDF, Excel, or Word)
  - `schema`: JSON string defining the fields to extract

**Response Format:**
```json
{
  "extracted_data": {
    "field1": "value1",
    "field2": "value2",
    "...": "..."
  },
  "file_info": {
    "filename": "example.pdf",
    "file_type": "pdf",
    "size": 12345,
    "saved_to": "extraction_results/example_20250710_123456.json"
  },
  "processing_time": 2.45,
  "status": "success"
}
```

#### 2. Health Check

```
GET /health
```

Returns the service's health status.

**Response Format:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-10T14:30:54"
}
```

#### 3. Supported Formats

```
GET /supported-formats
```

Returns a list of supported document formats.

**Response Format:**
```json
{
  "supported_formats": {
    "pdf": [".pdf"],
    "excel": [".xlsx", ".xls"],
    "word": [".docx", ".doc"]
  }
}
```

#### 4. Validate Schema

```
POST /validate-schema
```

Validates an extraction schema.

**Request Format:**
- Content-Type: `application/json`
- Body: JSON object mapping field names to descriptions

**Response Format:**
```json
{
  "valid": true,
  "fields": ["field1", "field2", "..."]
}
```

## Usage Examples

### Example 1: Extract information from a PDF document

**Python:**
```python
import requests
import json

# Define extraction schema
schema = {
    "company_name": "Name of the company",
    "financial_year": "Financial year of the report",
    "revenue": "Total revenue/sales",
    "net_profit": "Net profit/income"
}

# API endpoint
url = "http://localhost:8000/extract"

# Prepare multipart form data
files = {
    'file': ('financial_report.pdf', open('financial_report.pdf', 'rb'), 'application/pdf'),
    'schema': (None, json.dumps(schema))
}

# Send request
response = requests.post(url, files=files)
data = response.json()

# Process extracted data
if response.status_code == 200:
    print("Extraction successful!")
    print(f"Company Name: {data['extracted_data']['company_name']}")
    print(f"Revenue: {data['extracted_data']['revenue']}")
    print(f"Saved to: {data['file_info']['saved_to']}")
else:
    print(f"Error: {data}")
```

### Example 2: JavaScript/TypeScript Client

**JavaScript:**
```javascript
async function extractDocumentInfo(file, schema) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('schema', JSON.stringify(schema));
  
  try {
    const response = await fetch('http://localhost:8000/extract', {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error extracting document info:', error);
    throw error;
  }
}

// Usage example
const fileInput = document.getElementById('documentFile');
const submitButton = document.getElementById('submitButton');

submitButton.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) {
    alert('Please select a file');
    return;
  }
  
  const schema = {
    company_name: 'Name of the company',
    financial_year: 'Financial year of the report',
    revenue: 'Total revenue/sales'
  };
  
  try {
    const result = await extractDocumentInfo(file, schema);
    console.log('Extracted data:', result.extracted_data);
    // Update UI with results
  } catch (error) {
    console.error('Extraction failed:', error);
  }
});
```

### Example 3: cURL

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@financial_report.pdf" \
  -F 'schema={"company_name": "Name of the company", "revenue": "Total revenue/sales"}'
```

## Configuration

The service is configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| OPENAI_API_KEY | Your OpenAI API key | (required) |
| OPENAI_MODEL | OpenAI model to use | gpt-3.5-turbo |

Create a `.env` file in the project root or set these variables in your environment.

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- `400`: Bad request (e.g., invalid schema format)
- `415`: Unsupported media type (unsupported file format)
- `500`: Server error (processing error)

Error responses contain a `detail` field with information about the error:

```json
{
  "detail": "Error message here"
}
```

## Best Practices

1. **Define Precise Schemas**: Better results come from clear, specific field descriptions.
2. **Check File Formats**: Use the `/supported-formats` endpoint to ensure your document type is supported.
3. **Validate Schemas**: Use the `/validate-schema` endpoint to validate your schema before extraction.
4. **Error Handling**: Always implement proper error handling in your client applications.
5. **Large Files**: For large files, consider implementing progress tracking in your client application.

## Use Case Scenarios

### Use Case 1: Identifying and Processing Different Document Types

The Document Extraction Service can automatically identify and process various document formats:

1. **PDF Document Processing**
   - Upload any PDF document (financial reports, contracts, etc.)
   - The system automatically identifies the file as a PDF
   - Data is extracted according to your specified schema
   - Example screenshot: `screenshot_identify_file_type(pdf).png`

2. **Excel Document Processing**
   - Upload Excel spreadsheets (.xlsx, .xls)
   - The system identifies tabular data structure
   - Extracts structured information across multiple sheets
   - Example screenshot: `screenshot_identify_file_type(excel).png`

3. **Word Document Processing**
   - Upload Word documents (.docx, .doc)
   - The system processes formatted text and embedded tables
   - Extracts information from both paragraph text and tabular data
   - Example screenshot: `screenshot_identify_file_type(docx).png`

### Use Case 2: Web Interface Testing

The service includes a functional HTML interface for testing extractions:
   - Upload documents directly through a web browser
   - Define extraction schemas through the interface
   - View extracted results in real-time
   - Example screenshot: `functional_test_html.png`

### Use Case 3: Results Storage and Management

All extraction results are automatically saved for future reference:
   - Results are stored in structured JSON format
   - Timestamped filenames prevent overwriting previous extractions
   - Easily access historical extraction results
   - Example screenshot: `generated_output_storage.png`

These use cases demonstrate how the Document Extraction Service can be integrated into various workflows, from financial data processing to legal document analysis and general information extraction tasks.