# API Reference

This document provides detailed information about the MCP Studio API endpoints, request/response formats, and authentication.

## Base URL

All API endpoints are relative to the base URL:

```
https://api.mcp-studio.example.com/v1
```

For local development:
```
http://localhost:8000/api/v1
```

## Authentication

MCP Studio uses JWT (JSON Web Tokens) for authentication.

### Obtaining a Token

```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the `Authorization` header:
```
Authorization: Bearer your_token_here
```

## Rate Limiting

- **Rate Limit**: 1000 requests per hour per IP
- **Response Headers**:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when the limit resets (UTC timestamp)

## Endpoints

### Servers

#### List All Servers

```http
GET /api/v1/servers
```

**Response**
```json
{
  "items": [
    {
      "id": "server-123",
      "name": "Production Server",
      "status": "online",
      "last_seen": "2025-08-08T14:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

#### Get Server Details

```http
GET /api/v1/servers/{server_id}
```

**Response**
```json
{
  "id": "server-123",
  "name": "Production Server",
  "status": "online",
  "version": "1.0.0",
  "uptime": 86400,
  "endpoints": ["http://server1:8000"],
  "metadata": {
    "cpu_cores": 8,
    "memory_gb": 32,
    "python_version": "3.10.8"
  },
  "last_seen": "2025-08-08T14:30:00Z"
}
```

### Tools

#### List Available Tools

```http
GET /api/v1/tools
```

**Query Parameters**
- `server_id`: Filter tools by server ID
- `category`: Filter by tool category
- `search`: Search term

**Response**
```json
{
  "items": [
    {
      "id": "tool-456",
      "name": "text_generator",
      "description": "Generates text based on input",
      "category": "text",
      "enabled": true,
      "parameters": [
        {
          "name": "prompt",
          "type": "string",
          "required": true,
          "description": "Input prompt"
        },
        {
          "name": "max_length",
          "type": "integer",
          "required": false,
          "default": 100
        }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

#### Get Client Tools

```http
GET /api/v1/clients/{client_id}/tools
```

**Response**
```json
{
  "client_id": "cursor-ide",
  "total": 56,
  "tools": [
    {
      "name": "read_file",
      "description": "Read the contents of a file at the given path. Returns the file contents as a string.",
      "enabled": true,
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Path to the file to read"
          }
        },
        "required": ["path"]
      },
      "server_id": "filesystem-server",
      "server_name": "Filesystem Tools",
      "status": "available"
    }
  ]
}
```

#### Toggle Tool Enablement

```http
POST /api/v1/clients/{client_id}/tools/{tool_name}/toggle
Content-Type: application/json

{
  "enabled": true
}
```

**Response**
```json
{
  "client_id": "cursor-ide",
  "tool_name": "read_file",
  "enabled": true,
  "message": "Tool read_file enabled successfully"
}
```

#### Execute Tool

```http
POST /api/v1/tools/{tool_id}/execute
Content-Type: application/json

{
  "parameters": {
    "prompt": "Hello, world!",
    "max_length": 50
  }
}
```

**Response**
```json
{
  "execution_id": "exec-789",
  "status": "pending",
  "created_at": "2025-08-08T14:35:00Z"
}
```

### Executions

#### Get Execution Status

```http
GET /api/v1/executions/{execution_id}
```

**Response**
```json
{
  "id": "exec-789",
  "tool_id": "tool-456",
  "status": "completed",
  "created_at": "2025-08-08T14:35:00Z",
  "started_at": "2025-08-08T14:35:01Z",
  "completed_at": "2025-08-08T14:35:05Z",
  "result": {
    "output": "Hello, world! This is a generated response.",
    "tokens_used": 12,
    "execution_time_ms": 4000
  },
  "error": null
}
```

#### Stream Execution Output

```http
GET /api/v1/executions/{execution_id}/stream
```

**Response** (Server-Sent Events)
```
event: status
data: {"status": "running"}

event: output
data: {"chunk": "Hello"}

event: output
data: {"chunk": ", world!"}

event: done
data: {"status": "completed"}
```

## Error Handling

Errors are returned with appropriate HTTP status codes and a JSON response body:

```json
{
  "detail": [
    {
      "loc": ["string", 0],
      "msg": "string",
      "type": "string"
    }
  ]
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## WebSocket API

For real-time communication, MCP Studio provides a WebSocket endpoint:

```
ws://localhost:8000/ws/v1
```

### Authentication

Send an authentication message immediately after connection:

```json
{
  "type": "auth",
  "token": "your_jwt_token_here"
}
```

### Subscribing to Events

```json
{
  "type": "subscribe",
  "channel": "executions",
  "execution_id": "exec-789"
}
```

### Receiving Updates

```json
{
  "type": "execution_update",
  "data": {
    "execution_id": "exec-789",
    "status": "completed",
    "output": "..."
  }
}
```

## Pagination

List endpoints support pagination using query parameters:

- `page`: Page number (default: 1)
- `size`: Items per page (default: 20, max: 100)

**Example**
```
GET /api/v1/servers?page=2&size=10
```

## Filtering

Many list endpoints support filtering using query parameters:

```
GET /api/v1/tools?status=active&category=text
```

## Sorting

Sort results using the `sort` parameter:

```
GET /api/v1/executions?sort=-created_at  # Newest first
GET /api/v1/executions?sort=duration     # Shortest first
```

## Field Selection

Use the `fields` parameter to select specific fields:

```
GET /api/v1/servers?fields=id,name,status
```

## Versioning

API versioning is handled through the URL path (`/api/v1/...`). Breaking changes will result in a new version number.

## Deprecation Policy

- Endpoints will be marked as deprecated at least 6 months before removal
- Deprecated endpoints will continue to work during the deprecation period
- Notices about deprecation will be included in the API response headers
