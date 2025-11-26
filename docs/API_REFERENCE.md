# API Reference

Fluxion00API v0.0.1 - Adaptive agent framework with LLM and database access

**Base URL**: `http://localhost:8000`

**Authentication**: JWT tokens required for WebSocket connections. Tokens are created by News Nexus API and verified by Fluxion00API using shared `JWT_SECRET`.

---

## GET /health

Health check endpoint for monitoring service status.

**Authentication:** Not required

**Sample Request**:
```bash
curl http://localhost:8000/health
```

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "version": "0.0.1",
  "active_connections": 3
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| status | string | Service health status |
| version | string | API version |
| active_connections | integer | Number of active WebSocket connections |

---

## GET /api/info

Returns API metadata including available agent tools and configuration.

**Authentication:** Not required

**Sample Request**:
```bash
curl http://localhost:8000/api/info
```

**Response (200 OK)**:
```json
{
  "name": "Fluxion00API",
  "version": "0.0.1",
  "description": "Adaptive agent framework with LLM and database access",
  "llm_provider": "Ollama (mistral:instruct)",
  "available_tools": [
    "count_approved_articles",
    "search_approved_articles",
    "get_articles_by_user",
    "get_articles_by_date_range",
    "get_article_by_id",
    "list_approved_articles",
    "execute_custom_sql"
  ],
  "database": {
    "path": "/Users/nick/Documents/_databases/NewsNexus10",
    "name": "newsnexus10.db"
  }
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| name | string | API name |
| version | string | API version |
| description | string | API description |
| llm_provider | string | LLM provider and model |
| available_tools | array | List of agent tool names |
| database | object | Database configuration |

---

## WebSocket /ws/{client_id}

WebSocket endpoint for real-time chat with LLM agent. Supports conversation history, tool execution, and streaming responses.

**Authentication:** Required (JWT token)

**URL Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| client_id | string | Yes | Unique client identifier (UUID recommended) |
| token | string | Yes | JWT token from News Nexus API (query parameter) |

**Connection Example**:
```javascript
const clientId = crypto.randomUUID();
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";
const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}?token=${token}`);

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message);
};
```

**Authentication Errors**:
```
WebSocket close code 4001: "Authentication required: missing token"
WebSocket close code 4001: "Authentication failed: Invalid token"
WebSocket close code 4000: "Authentication error: <error details>"
```

**Behavior**:
- Each connection creates a new Agent instance with independent conversation history
- Token must be valid JWT signed with `JWT_SECRET` containing `{ id: <user_id> }`
- User ID is verified against Users table in database
- Connection rejected before acceptance if authentication fails

---

## WebSocket Message Types

### Client → Server Messages

#### user_message
Send user message to agent for processing.

```json
{
  "type": "user_message",
  "content": "How many articles have been approved?"
}
```

**Response Flow**:
1. `user_echo` - Acknowledges message receipt
2. `typing` - Indicates agent is processing (content: true)
3. `agent_message` - Agent's response
4. `typing` - Processing complete (content: false)

#### clear_history
Clear conversation history for current connection.

```json
{
  "type": "clear_history"
}
```

**Response**:
```json
{
  "type": "system",
  "content": "Conversation history cleared"
}
```

#### ping
Keep-alive ping message.

```json
{
  "type": "ping"
}
```

**Response**:
```json
{
  "type": "pong"
}
```

---

### Server → Client Messages

#### system
System messages (connection status, notifications).

```json
{
  "type": "system",
  "content": "Welcome nickrodriguez! Connected to Fluxion00API. How can I help you today?"
}
```

#### user_echo
Acknowledges receipt of user message.

```json
{
  "type": "user_echo",
  "content": "How many articles have been approved?"
}
```

#### typing
Indicates agent processing status.

```json
{
  "type": "typing",
  "content": true
}
```

#### agent_message
Agent's response to user message.

```json
{
  "type": "agent_message",
  "content": "The number of approved articles is 3743."
}
```

#### error
Error message from agent or system.

```json
{
  "type": "error",
  "content": "Error processing message: Connection timeout"
}
```

---

## Agent Tools

The agent has access to the following database query tools:

### count_approved_articles
Count articles by approval status.

**Parameters**:
- `is_approved` (boolean, optional, default: true) - True for approved, false for rejected

### search_approved_articles
Search articles by text across headlines, publication names, article text, and notes.

**Parameters**:
- `search_text` (string, required) - Text to search for
- `is_approved` (boolean, optional, default: true) - Filter by approval status
- `limit` (integer, optional, default: 10) - Maximum results

### get_articles_by_user
Get articles approved or reviewed by specific user.

**Parameters**:
- `user_id` (integer, required) - User ID
- `is_approved` (boolean, optional, default: true) - Filter by approval status
- `limit` (integer, optional, default: 10) - Maximum results

### get_articles_by_date_range
Get articles within date range.

**Parameters**:
- `start_date` (string, optional) - Start date (YYYY-MM-DD format)
- `end_date` (string, optional) - End date (YYYY-MM-DD format)
- `is_approved` (boolean, optional, default: true) - Filter by approval status
- `limit` (integer, optional, default: 10) - Maximum results

### get_article_by_id
Get specific article by ArticleApproved ID.

**Parameters**:
- `article_approved_id` (integer, required) - Article ID

### list_approved_articles
Get paginated list of articles.

**Parameters**:
- `is_approved` (boolean, optional, default: true) - Filter by approval status
- `limit` (integer, optional, default: 10) - Maximum results
- `offset` (integer, optional, default: 0) - Pagination offset

### execute_custom_sql
Text-to-SQL fallback tool for questions not covered by pre-defined tools. Agent generates SQL query based on natural language question.

**Parameters**:
- `question` (string, required) - Natural language question

**Security**:
- Only SELECT queries allowed
- Read-only database connection
- Multi-layer validation (keyword blocklist, structural validation, complexity limits)
- Maximum 1000 rows returned

---

## Error Handling

### HTTP Errors

**500 Internal Server Error**:
```json
{
  "detail": "Internal server error"
}
```

### WebSocket Errors

**Authentication Failure** (Close code 4001):
- Missing token
- Invalid token signature
- User not found in database

**General Error** (Close code 4000):
- Unexpected authentication error

**Application Errors** (sent as message):
```json
{
  "type": "error",
  "content": "Error processing message: <error details>"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. Future versions may include:
- Connection limits per user
- Message rate limits
- Token refresh requirements

---

## CORS Configuration

CORS is enabled for all origins (`allow_origins: ["*"]`). In production, this should be restricted to specific origins.

---

## Environment Variables

Required environment variables:
- `JWT_SECRET` - Shared secret for JWT verification (matches News Nexus API)
- `PATH_TO_DATABASE` - Database directory path
- `NAME_DB` - Database filename
- `URL_BASE_OLLAMA` - Ollama API endpoint
- `KEY_OLLAMA` - Ollama API key (optional)
- `PORT` - Server port (default: 8000)
