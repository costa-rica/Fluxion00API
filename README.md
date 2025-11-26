# Fluxion00API

Fluxion00API is an adaptive agent framework that powers a chat interface connected to LLMs with direct access to project databases and documents. It provides a modular, high‑performance backend for building intelligent, context‑aware systems that can query data, interpret resources, and respond in real time.

## .env

```
NAME_APP=Fluxion00API
PATH_TO_DATABASE=/Users/nick/Documents/_databases/Fluxion00API
NAME_DB=fluxion00.db
PATH_TO_PYTHON_VENV=/Users/nick/Documents/_environments/fluxion
PATH_TO_DOCUMENTS=/Users/nick/Documents/_project_resources/Fluxion00API/docs_for_agent
URL_BASE_OLLAMA=https://fell-st-ollama.dashanddata.com
KEY_OLLAMA=SECRET_KEY
URL_BASE_OPENAI=https://api.openai.com/v1
KEY_OPENAI=SECRET_KEY
```

## References

- [SQL_SCHEMA.md](docs/SQL_SCHEMA.md): This document has the database schema for this specific project.

## Quick Start

1. Activate virtual environment: `source /Users/nick/Documents/_environments/fluxion/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Start the server: `python run.py`
4. Open your browser to: `http://localhost:8000`

## Run Tests

1. Activate venv: `source /Users/nick/Documents/_environments/fluxion/bin/activate`
2. Database queries: `python test_queries.py`
3. Ollama integration: `python test_ollama.py`
4. Agent system: `python test_agent.py`

## Development

### Purpose

Fluxion00API provides a unified backend for adaptive agents that can query databases, interpret project documents, and generate intelligent responses through a chat interface.

### High‑Level Architecture

The system consists of a FastAPI backend with WebSocket chat endpoints, an agent layer that routes requests to tools, and a modular knowledge base that accesses databases and documents through interchangeable adapters.

### Tech Stack Summary

- Python 3.x
- FastAPI (async)
- Raw SQL or SQLAlchemy Core
- OpenAI API + local Ollama (Mistral:instruction) LLM provider switching

### Development Constraints

- Versioning begins at `00`
- Agents live inside Fluxion00API for this version
- Internal minimal UI allowed for development testing
- All SQL query functions must include automated tests
- LLM providers must be swappable via configuration

## Goals for Version 00

- Implement chat endpoint with WebSocket support
- Build initial agent layer with modular knowledge adapters
- Add raw SQL query utilities with tests
- Support switching between OpenAI and local Ollama
- Provide minimal internal chat UI for development
