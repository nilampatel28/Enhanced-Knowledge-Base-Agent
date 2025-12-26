# Enhanced Knowledge Base Agent - REST API

## Overview

The REST API provides programmatic access to all Enhanced Knowledge Base Agent functionality. The API is built with Flask and follows RESTful conventions.

## Running the Server

### Using the Web Server

```bash
python -m enhanced_kb_agent.web.server --host 0.0.0.0 --port 5000 --debug
```

### Programmatically

```python
from enhanced_kb_agent.web.server import create_web_app
from enhanced_kb_agent.config import KnowledgeBaseConfig

config = KnowledgeBaseConfig()
app = create_web_app(config)
app.run(host='0.0.0.0', port=5000, debug=False)
```

## API Endpoints

### Health Check

**GET** `/api/health`

Check if the API is running.

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00.000000"
}
```

### Configuration

**GET** `/api/config`

Get the current knowledge base configuration.

**Response:**
```json
{
    "kb_id": "...",
    "kb_name": "enhanced-kb",
    "cache_enabled": true,
    "enable_versioning": true,
    ...
}
```

## Query Endpoints

### Execute Query

**POST** `/api/query`

Execute a complex query that may require multiple retrieval steps.

**Request:**
```json
{
    "query": "What is the relationship between X and Y?"
}
```

**Response:**
```json
{
    "query": "What is the relationship between X and Y?",
    "answer": "The relationship between X and Y is...",
    "sources": ["source1", "source2"],
    "confidence": 0.95,
    "reasoning_steps": [
        {
            "step_number": 1,
            "query": "Find information about X",
            "results_count": 5,
            "execution_time_ms": 150.5,
            "success": true,
            "error_message": ""
        }
    ],
    "conflicts_detected": []
}
```

## Storage Endpoints

### Store Content

**POST** `/api/store`

Store new information in the knowledge base.

**Request:**
```json
{
    "content": "The content to store",
    "content_type": "text/plain",
    "metadata": {
        "title": "Content Title",
        "description": "Content description",
        "tags": ["tag1", "tag2"],
        "categories": ["category1"],
        "source": "web-ui"
    }
}
```

**Response:**
```json
{
    "content_id": "abc123",
    "version": 1,
    "created_at": "2024-01-15T10:30:00.000000",
    "message": "Content stored successfully"
}
```

### Update Content

**PUT** `/api/update/<content_id>`

Update existing information.

**Request:**
```json
{
    "content": "Updated content",
    "change_reason": "Corrected information"
}
```

**Response:**
```json
{
    "content_id": "abc123",
    "version": 2,
    "updated_at": "2024-01-15T10:35:00.000000",
    "message": "Content updated successfully"
}
```

## Version History Endpoints

### Get Version History

**GET** `/api/versions/<content_id>`

Retrieve the version history for a piece of content.

**Query Parameters:**
- `limit` (optional): Maximum number of versions to return (default: 10)
- `offset` (optional): Number of versions to skip (default: 0)

**Response:**
```json
{
    "content_id": "abc123",
    "versions": [
        {
            "version_number": 1,
            "created_at": "2024-01-15T10:30:00.000000",
            "changed_by": "user1",
            "change_reason": "Initial creation"
        },
        {
            "version_number": 2,
            "created_at": "2024-01-15T10:35:00.000000",
            "changed_by": "user1",
            "change_reason": "Corrected information"
        }
    ],
    "total_versions": 2,
    "returned_versions": 2
}
```

## Category Endpoints

### Get All Categories

**GET** `/api/categories`

Retrieve all categories.

**Response:**
```json
{
    "categories": [
        {
            "id": "cat1",
            "name": "Technology",
            "description": "Technology-related content",
            "content_count": 15
        }
    ]
}
```

### Create Category

**POST** `/api/categories`

Create a new category.

**Request:**
```json
{
    "name": "New Category",
    "description": "Category description",
    "parent_category": "parent_id" (optional)
}
```

**Response:**
```json
{
    "id": "cat2",
    "name": "New Category",
    "message": "Category created successfully"
}
```

## Tag Endpoints

### Get All Tags

**GET** `/api/tags`

Retrieve all tags.

**Response:**
```json
{
    "tags": [
        {
            "id": "tag1",
            "name": "important",
            "usage_count": 25
        }
    ]
}
```

## Search Endpoints

### Search

**POST** `/api/search`

Search for content by query, tags, or categories.

**Request:**
```json
{
    "query": "search term" (optional),
    "tags": ["tag1", "tag2"] (optional),
    "categories": ["category1"] (optional)
}
```

**Response:**
```json
{
    "results": [
        {
            "content_id": "abc123",
            "title": "Result Title",
            "relevance": 0.95
        }
    ],
    "total_results": 1
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **201**: Created
- **400**: Bad Request (missing or invalid parameters)
- **404**: Not Found
- **500**: Internal Server Error

Error responses include an error message:

```json
{
    "error": "Error description",
    "message": "Additional details"
}
```

## Authentication

Currently, the API does not require authentication. In production, implement appropriate authentication mechanisms.

## Rate Limiting

Currently, the API does not implement rate limiting. In production, consider implementing rate limiting to prevent abuse.

## CORS

Currently, CORS is not configured. In production, configure CORS appropriately for your use case.

## Examples

### Python

```python
import requests

# Query
response = requests.post('http://localhost:5000/api/query', json={
    'query': 'What is machine learning?'
})
print(response.json())

# Store
response = requests.post('http://localhost:5000/api/store', json={
    'content': 'Machine learning is...',
    'metadata': {
        'title': 'ML Definition',
        'tags': ['ml', 'ai']
    }
})
print(response.json())
```

### cURL

```bash
# Query
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'

# Store
curl -X POST http://localhost:5000/api/store \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Machine learning is...",
    "metadata": {"title": "ML Definition"}
  }'
```

### JavaScript

```javascript
// Query
fetch('/api/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query: 'What is machine learning?'})
})
.then(r => r.json())
.then(data => console.log(data));

// Store
fetch('/api/store', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        content: 'Machine learning is...',
        metadata: {title: 'ML Definition'}
    })
})
.then(r => r.json())
.then(data => console.log(data));
```
