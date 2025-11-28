# Production Environment Setup for Fluxion00API

This document explains how the Fluxion00API service is deployed in production, how environment variables are loaded, how PM2 manages the process, and why the `run.py` launcher is used instead of calling Uvicorn directly. This file provides essential context for any developer maintaining or deploying the system.

---

## Overview

Fluxion00API is a FastAPI application with WebSocket support, tool‑routing agents, and a modular knowledge base layer. In production, the application must run under an ASGI server capable of handling asynchronous requests and WebSockets. We use **Uvicorn** for this purpose.

However, Uvicorn **does not** load `.env` files by itself. This has implications for how we run the application in a PM2‑managed environment.

---

## Why We Use `run.py` in Production

Locally, developers often run:

```
python run.py
```

This works because **run.py loads environment variables using `python-dotenv`**:

```python
from dotenv import load_dotenv
load_dotenv(override=True)
```

In early versions of the production setup, PM2 launched Uvicorn directly:

```
script: "/path/to/uvicorn"
args: "src.api.app:app --host 0.0.0.0 --port 8005 --workers 3"
```

This caused `.env` variables to **not load at all**, because:

- Uvicorn does _not_ automatically load `.env`
- PM2 does not apply `.env` files to Python processes
- Therefore, FastAPI never saw variables like `PATH_TO_DATABASE`, `JWT_SECRET`, etc.

By switching PM2 to run the application **through `run.py`**, the `.env` loading becomes part of the startup process.

This guarantees:

- Consistent behavior between development and production
- Secrets are stored in `.env`, not inside PM2 config files
- No reliance on shell‑inherited env variables
- Uvicorn still runs exactly as before (handled by run.py)

---

## PM2 Configuration

Production PM2 entry uses Python as the script and `run.py` as the argument.

**Use the provided `ecosystem.config.js` file:**

```bash
pm2 start ecosystem.config.js
```

The configuration file (located in project root) contains:

```javascript
{
  name: "Fluxion00API",
  script: "run.py",
  interpreter: "/home/nick/environments/fluxion/bin/python3",
  cwd: "/home/nick/applications/Fluxion00API/",
  env: {
    PORT: "8005",
    HOST: "0.0.0.0",
    RELOAD: "false"
  }
}
```

### Why this works

- PM2 starts Python
- Python executes `run.py`
- `run.py` loads `.env`
- `run.py` then starts Uvicorn (the actual ASGI server)

PM2 still:

- Runs in the background
- Logs stdout/stderr
- Restarts on crash
- Enables `pm2 logs`, `pm2 restart`, etc.

### Belt-and-Suspenders: Dual .env Loading

As of the latest version, `.env` files are loaded in **two places**:

1. **`run.py`** - Loads .env when run directly (e.g., `python run.py`)
2. **`src/__init__.py`** - Loads .env when ANY src module is imported

This dual approach ensures environment variables are always available, even if:
- PM2 is misconfigured to call uvicorn directly
- The application is imported as a module from another script
- Tests import modules without going through run.py

The `src/__init__.py` loader acts as a safety net and will be the first code executed when uvicorn imports `src.api.app:app`.

---

## Environment Variables

All sensitive or environment‑specific values live in the `.env` file located at:

```
/home/nick/applications/Fluxion00API/.env
```

Example structure:

```
NAME_APP=Fluxion00API
PATH_TO_DATABASE=/home/nick/databases/NewsNexus10/
JWT_SECRET=SECRET
NAME_DB=newsnexus10.db
PATH_TO_PYTHON_VENV=/home/nick/environments/fluxion
PATH_TO_DOCUMENTS=/home/nick/project_resources/Fluxion00API/docs_for_agent
URL_BASE_OLLAMA=https://fell-st-ollama.dashanddata.com
KEY_OLLAMA=SECRET
URL_BASE_OPENAI=https://api.openai.com/v1
KEY_OPENAI=SECRET
```

These values are automatically loaded at startup by `run.py`.

---

## Uvicorn in Production

Using `run.py` **does not bypass Uvicorn**.

Uvicorn is still the ASGI server running the app; the only difference is the entrypoint:

- Direct method (NOT used):  
  `uvicorn src.api.app:app ...`

- Indirect method via run.py (USED):  
  `python run.py  →  uvicorn.run(...)`

This keeps the system aligned with the standard FastAPI deployment model.

---

## Development vs. Production

| Environment | Entry Command      | Loads `.env`? | Hot Reload? |
| ----------- | ------------------ | ------------- | ----------- |
| Dev         | `python run.py`    | ✔ via dotenv  | ✔ enabled   |
| Prod        | `pm2 start run.py` | ✔ via dotenv  | ❌ disabled |

---

## Summary

- **Uvicorn is still the production ASGI server.**
- **PM2 now runs Python instead of Uvicorn directly.**
- **`.env` file is required and loaded via `python-dotenv`.**
- **This approach ensures reliable, consistent configuration across environments.**
- **No secrets are stored in `ecosystem.config.js`.**

This setup is intentionally explicit and maintainable, and should be followed for all future Python/ASGI services deployed through PM2.

---

## Troubleshooting

### Error: "Database path and name must be provided either as arguments or through PATH_TO_DATABASE and NAME_DB environment variables"

**Symptom:** Application crashes on startup with `ValueError` about missing database configuration.

**Cause:** The `.env` file is not being loaded before the application imports the database module.

**Solutions:**

1. **Verify PM2 is using run.py** - Check your PM2 configuration:
   ```bash
   pm2 describe Fluxion00API
   ```
   The `script` field should show `run.py`, NOT `uvicorn`.

2. **Use the provided ecosystem.config.js**:
   ```bash
   pm2 stop Fluxion00API
   pm2 delete Fluxion00API
   pm2 start ecosystem.config.js
   pm2 save
   ```

3. **Verify .env file exists and has correct permissions**:
   ```bash
   ls -la /home/nick/applications/Fluxion00API/.env
   cat /home/nick/applications/Fluxion00API/.env
   ```

4. **Check that python-dotenv is installed**:
   ```bash
   source /home/nick/environments/fluxion/bin/activate
   pip list | grep python-dotenv
   ```
   If not installed, run:
   ```bash
   pip install python-dotenv==1.0.0
   ```

5. **Test that .env loads correctly**:
   ```bash
   source /home/nick/environments/fluxion/bin/activate
   cd /home/nick/applications/Fluxion00API
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(f'DB Path: {os.getenv(\"PATH_TO_DATABASE\")}'); print(f'DB Name: {os.getenv(\"NAME_DB\")}')"
   ```
   This should print your database path and name.

### PM2 Shows "Waiting for child process died"

**Cause:** Application crashed during startup, usually due to missing environment variables or import errors.

**Solution:**
1. Check PM2 logs for the full error:
   ```bash
   pm2 logs Fluxion00API --lines 100
   ```

2. Test the application directly first:
   ```bash
   source /home/nick/environments/fluxion/bin/activate
   cd /home/nick/applications/Fluxion00API
   python run.py
   ```
   This will show errors immediately without PM2 interfering.

### Changes to .env Not Taking Effect

**Cause:** PM2 caches the environment from initial startup.

**Solution:**
```bash
pm2 restart Fluxion00API
```
Or for a hard restart:
```bash
pm2 stop Fluxion00API
pm2 start ecosystem.config.js
```

---

If anything in this document becomes outdated or if deployment methods change (e.g., moving to systemd or Docker), update this file accordingly.
