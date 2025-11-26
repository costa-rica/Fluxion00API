# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Fluxion00API is an adaptive agent framework that provides a chat interface with LLM-powered agents that can query databases in real-time. The system uses FastAPI with WebSocket support, a custom agent orchestration layer, and connects to an Ollama LLM endpoint.

**Key architectural principle**: All components are swappable and modular. LLM providers, database query functions, and agent tools are designed for easy extension.

## Development Environment

**Virtual Environment Location**: `/Users/nick/Documents/_environments/fluxion`

Always activate before working:

```bash
source /Users/nick/Documents/_environments/fluxion/bin/activate
```

**Database Location**: The project connects to an external NewsNexus10 SQLite database at `/Users/nick/Documents/_databases/NewsNexus10/newsnexus10.db`. This is NOT a local database file - it's a shared resource defined in `.env`.

**Environment Variables**: The `.env` file is gitignored and contains:

- `PATH_TO_DATABASE` and `NAME_DB` - Database location
- `URL_BASE_OLLAMA` and `KEY_OLLAMA` - Ollama API endpoint
- See README.md for full list

## Running the Application

**Start the server**:

```bash
python run.py
```

Then open `http://localhost:8000` for the chat interface.

**Run test suites** (in order of dependency):

```bash
python test_queries.py    # Database layer (7 tests)
python test_ollama.py     # LLM integration (7 tests)
python test_agent.py      # Agent system (8 tests)
```

Each test suite is comprehensive and provides detailed output. All tests must pass before committing.

## Architecture: Four-Layer Design

### 1. Database Layer (`src/database/`, `src/queries/`)

**Connection**: `src/database/connection.py` provides a `DatabaseConnection` class with context managers for SQLite operations. Always use `get_db()` to access the global connection instance.

**Database Schema**: The database schema is defined in `docs/SQL_SCHEMA.md`.

**Query Functions**: Located in `src/queries/queries_approved_articles.py`. All query functions:

- Use raw SQL (no ORM) via `sqlite3`
- Return dictionaries (not model objects)
- Include proper error handling
- Must have corresponding tests in `test_queries.py`

**Adding new query functions**:

1. Create function in appropriate `src/queries/queries_*.py` file
2. Use Python naming conventions for files: `queries_approved_articles.py` (underscores, not hyphens)
3. Add tests to corresponding `test_*.py` file
4. Functions can query multiple tables but organize by primary table

### 2. LLM Layer (`src/llm/`)

**Provider Architecture**: `src/llm/base.py` defines `BaseLLMProvider` abstract class. All LLM providers inherit from this.

**Current Implementation**: `OllamaProvider` in `src/llm/ollama_client.py` connects to remote Ollama instance (Mistral:instruct model).

**Key Methods**:

- `generate()` - Single prompt completion
- `chat()` - Conversation with message history
- `stream_generate()` - Streaming responses for real-time UI

**Adding new LLM providers** (e.g., OpenAI):

1. Create new file in `src/llm/` (e.g., `openai_client.py`)
2. Inherit from `BaseLLMProvider`
3. Implement all abstract methods
4. Update `src/llm/__init__.py` exports
5. Add tests following `test_ollama.py` pattern

**Note**: Ollama API uses `/api/generate` endpoint (not chat endpoint). The `chat()` method internally converts messages to single prompts.

### 3. Agent Layer (`src/agent/`)

**Tool System**: Custom implementation (not LangChain). Tools are Python functions wrapped with metadata:

- `src/agent/tools.py` - Core `Tool`, `ToolParameter`, and `ToolRegistry` classes
- `src/agent/tools_articles.py` - Article query function wrappers
- `src/agent/agent.py` - Main `Agent` orchestration class

**How Tool Execution Works**:

1. Agent receives user message
2. LLM analyzes message and decides if tools are needed
3. LLM responds with structured `TOOL_CALL:` format
4. Agent parses response, executes tool via `ToolRegistry`
5. Tool results are formatted and sent back to LLM
6. LLM generates final user-facing response

**Tool Call Format** (parsed by `Agent._parse_tool_call()`):

```
TOOL_CALL: tool_name
ARGUMENTS:
{
  "param1": "value1",
  "param2": value2
}
END_TOOL_CALL
```

**Adding new tools**:

1. Create wrapper function in appropriate `src/agent/tools_*.py` file
2. Register with `registry.register_function()` including `ToolParameter` definitions
3. Tools can be sync or async (agent detects with `inspect.iscoroutinefunction`)
4. Format results appropriately (use helper functions like `format_articles_list`)

**Agent System Prompt**: Automatically generated in `Agent._default_system_prompt()` and includes all registered tools. The agent is told it has database access and how to use tools.

### 4. API Layer (`src/api/`)

**FastAPI App**: `src/api/app.py` defines main application with:

- Static file serving from `src/static/`
- WebSocket endpoint at `/ws/{client_id}`
- Health check at `/health`
- API info at `/api/info`

**WebSocket Handler**: `src/api/websocket.py` manages:

- `ConnectionManager` - Tracks active WebSocket connections and their agents
- Each connection gets its own `Agent` instance
- Message types: `user_message`, `agent_message`, `system`, `error`, `typing`, `ping/pong`

**Important**: Each WebSocket connection creates a new LLM provider and agent instance. This is stateful - conversation history is maintained per connection.

**Web UI**: Located in `src/static/` with:

- `index.html` - Main chat interface
- `css/style.css` - Styling with gradient purple theme
- `js/chat.js` - WebSocket client with auto-reconnection

## Development Constraints (Version 00)

- **Versioning**: All version numbers begin at `00` (not 1.0)
- **Agent Location**: Agents live inside this FastAPI app (not separate service)
- **SQL Testing**: All query functions MUST have automated tests
- **LLM Swappability**: Provider architecture must support easy swapping
- **File Naming**: Python conventions - use underscores (e.g., `queries_approved_articles.py`)
- **Module Structure**: All code in `src/` directory with proper `__init__.py` exports

## Common Workflows

**Adding a new database table support**:

1. Check `docs/DATABASE_OVERVIEW.md` for table schema
2. Create query functions in `src/queries/queries_<table_name>.py`
3. Add tests in `test_queries.py`
4. Create tool wrappers in `src/agent/tools_<category>.py`
5. Register tools (can add to existing or new registry call)

**Debugging WebSocket issues**:

- Check browser console for WebSocket connection errors
- Server logs show connection/disconnection events
- Each client has unique ID - useful for tracking specific connections
- `ConnectionManager.get_connection_count()` shows active connections

**Testing LLM integration**:

- `test_ollama.py` includes connection test, generation, chat, streaming
- Tests run against live Ollama endpoint (requires network)
- Temperature variation test useful for debugging model behavior

## Important Files

- `docs/DATABASE_OVERVIEW.md` - Complete database schema (TypeScript/Sequelize models)
- `run.py` - Application entry point (uses uvicorn)
- `requirements.txt` - All dependencies with pinned versions
- `.env` - Configuration (gitignored, see README for template)

## Database Schema Notes

The database contains NewsNexus10 article data with these key tables:

- `ArticleApproveds` - Article approval workflow (primary focus)
- `Articles` - Core article storage
- `Users` - User management for approvals
- `States` - US geographic states for filtering
- Many junction tables for relationships

**Critical**: This is a TypeScript/Sequelize database created by another project. Python code accesses it read-only via raw SQL. Do not attempt to modify schema from this codebase.
