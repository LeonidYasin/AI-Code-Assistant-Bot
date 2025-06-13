# API Documentation

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Project Management](#project-management)
  - [Code Analysis](#code-analysis)
  - [LLM Integration](#llm-integration)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## Overview

This document describes the API for the AI Code Assistant bot. The API follows REST conventions and returns JSON-encoded responses.

## Authentication

All API requests require an API key, which should be included in the `X-API-Key` header.

```http
GET /api/v1/projects HTTP/1.1
Host: api.aicodeassistant.com
X-API-Key: your_api_key_here
```

## Endpoints

### Project Management

#### List Projects

```http
GET /api/v1/projects
```

**Response**
```json
{
  "projects": [
    {
      "id": "project-123",
      "name": "Example Project",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### Create Project

```http
POST /api/v1/projects
Content-Type: application/json

{
  "name": "New Project"
}
```

**Response**
```json
{
  "id": "project-456",
  "name": "New Project",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

### Code Analysis

#### Analyze Code

```http
POST /api/v1/analyze
Content-Type: application/json

{
  "code": "def example():\n    pass",
  "language": "python"
}
```

**Response**
```json
{
  "analysis": {
    "complexity": "low",
    "issues": [],
    "suggestions": [
      "Add docstring to function 'example'"
    ]
  }
}
```

### LLM Integration

#### Generate Code

```http
POST /api/v1/generate
Content-Type: application/json

{
  "prompt": "Create a Python function that calculates factorial",
  "temperature": 0.7
}
```

**Response**
```json
{
  "generated_code": "def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n - 1)",
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 25,
    "total_tokens": 40
  }
}
```

## Error Handling

Errors follow the following format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional error details"
    }
  }
}
```

Common error codes:
- `400`: Bad Request - Invalid request format
- `401`: Unauthorized - Invalid or missing API key
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Something went wrong on our end

## Rate Limiting

- Free tier: 100 requests per hour
- Pro tier: 10,000 requests per hour

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 3600
```

## Examples

### Python Example

```python
import requests

API_KEY = "your_api_key_here"
BASE_URL = "https://api.aicodeassistant.com/api/v1"

def list_projects():
    response = requests.get(
        f"{BASE_URL}/projects",
        headers={"X-API-Key": API_KEY}
    )
    response.raise_for_status()
    return response.json()

def analyze_code(code, language="python"):
    response = requests.post(
        f"{BASE_URL}/analyze",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={"code": code, "language": language}
    )
    response.raise_for_status()
    return response.json()
```

### cURL Example

```bash
# List projects
curl -X GET \
  -H "X-API-Key: $API_KEY" \
  https://api.aicodeassistant.com/api/v1/projects

# Analyze code
curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"code": "def example():\n    pass", "language": "python"}' \
  https://api.aicodeassistant.com/api/v1/analyze
```
