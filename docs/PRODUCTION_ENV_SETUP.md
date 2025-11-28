# Production Environment Setup

This document describes the complete production deployment configuration for Fluxion00API, including process management, web server configuration, and environment variable handling.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Uvicorn in Production](#uvicorn-in-production)
- [PM2 Process Management](#pm2-process-management)
- [Nginx Reverse Proxy](#nginx-reverse-proxy)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Development vs Production](#development-vs-production)

---

## Environment Variables

### .env File Location

The `.env` file is stored in the **project root directory** on both development and production servers:

```
/home/nick/applications/Fluxion00API/.env  (production)
/Users/nick/Documents/Fluxion00API/.env     (development)
```

### Example .env File

```bash
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

### Why .env Loading Works in Production

The current setup works reliably in production because of **dual-layer .env loading**:

#### Layer 1: Package Initialization (Always Active)

When Python imports any module from the `src` package, `src/__init__.py` automatically executes:

```python
# src/__init__.py
from dotenv import load_dotenv
from pathlib import Path

# Find .env file in project root (parent of src/)
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(dotenv_path=env_file, override=True)
```

**This happens automatically whenever you import ANY module from `src`**, including:

- `from src.api.app import app` (used by PM2/uvicorn)
- `from src.database import get_db`
- `from src.agent import Agent`

#### Layer 2: run.py (Development Convenience)

The `run.py` script provides an additional layer of .env loading for development:

```python
# run.py
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)
```

**Why dual loading is beneficial**:

1. **Production (PM2)**: Uvicorn directly imports `src.api.app:app`, triggering `src/__init__.py` to load .env
2. **Development (run.py)**: Extra load_dotenv() call ensures variables are available even before importing src
3. **Testing**: Test scripts import src modules and automatically get environment variables

**The key insight**: As long as the .env file is in the project root and PM2's `cwd` (current working directory) is set to the project root, the package initialization will find and load the .env file.

---

## Uvicorn in Production

### What is Uvicorn?

Uvicorn is an ASGI (Asynchronous Server Gateway Interface) server implementation for Python. It's the recommended server for FastAPI applications because:

- High performance with async/await support
- WebSocket support (critical for Fluxion00API's real-time chat)
- Multi-worker process management
- Low memory footprint

### Development vs Production Mode

#### Development Mode (via run.py)

```bash
python run.py
```

**How it works**:

1. `run.py` loads .env file using `python-dotenv`
2. Reads configuration from environment variables (HOST, PORT, RELOAD)
3. Starts uvicorn with `reload=True` (auto-restart on file changes)
4. Single worker process
5. Listens on `0.0.0.0:8000` by default

```python
# run.py configuration
uvicorn.run(
    "src.api.app:app",    # Import path to FastAPI app
    host="0.0.0.0",       # Accept connections from any network interface
    port=8000,            # Development port
    reload=True,          # Auto-reload on code changes
    log_level="info"      # Verbose logging
)
```

#### Production Mode (via PM2 + Uvicorn)

```bash
pm2 start ecosystem.config.js
```

**How it works**:

1. PM2 launches uvicorn binary directly (not through run.py)
2. Uvicorn imports `src.api.app:app`, triggering `src/__init__.py` to load .env
3. Multiple worker processes (3 workers in production)
4. No auto-reload (stability and performance)
5. Listens on `0.0.0.0:8005`

**Why direct uvicorn invocation**:

- **Faster startup**: No Python interpreter overhead from run.py
- **Process control**: PM2 manages the master process directly
- **Worker management**: Uvicorn's `--workers` flag enables multi-processing
- **Signal handling**: PM2 can send signals directly to uvicorn for graceful shutdown

**Worker processes**: The `--workers 3` flag creates 3 separate Python processes:

- Each worker can handle multiple concurrent requests (async)
- Load balancing across workers handled by uvicorn
- Ideal for CPU-bound operations and high traffic

---

## PM2 Process Management

### ecosystem.config.js Configuration

PM2 uses an ecosystem configuration file to define application settings. For Fluxion00API:

```javascript
    {
      name: "Fluxion00API",
      script: "/home/nick/environments/fluxion/bin/uvicorn",
      args: "src.api.app:app --host 0.0.0.0 --port 8005 --workers 3",
      cwd: "/home/nick/applications/Fluxion00API/",
      interpreter: "/home/nick/environments/fluxion/bin/python3",
      env: {
        PORT: 8005, // The port the app will listen on
      },
    },
```

### Configuration Breakdown

| Parameter     | Value                                                    | Purpose                                                   |
| ------------- | -------------------------------------------------------- | --------------------------------------------------------- |
| `name`        | "Fluxion00API"                                           | Process identifier in PM2                                 |
| `script`      | `/home/nick/environments/fluxion/bin/uvicorn`            | Direct path to uvicorn binary in virtualenv               |
| `args`        | `src.api.app:app --host 0.0.0.0 --port 8005 --workers 3` | Arguments passed to uvicorn                               |
| `cwd`         | `/home/nick/applications/Fluxion00API/`                  | Working directory (where .env is located)                 |
| `interpreter` | `/home/nick/environments/fluxion/bin/python3`            | Python interpreter from virtualenv                        |
| `env.PORT`    | 8005                                                     | Environment variable (redundant with --port but explicit) |

### Key Points

**Why `cwd` is critical**:

- PM2 changes to this directory before launching the process
- `src/__init__.py` uses `Path(__file__).parent.parent` to find project root
- When cwd is the project root, this resolves correctly to where .env is located
- All relative paths in the application work correctly

**Why specify `interpreter`**:

- Ensures the correct Python virtualenv is used
- All dependencies installed in `/home/nick/environments/fluxion` are available
- Avoids system Python conflicts

**Why use virtualenv's uvicorn binary**:

- Ensures correct uvicorn version
- Prevents global vs. local package conflicts
- Explicit about which environment is running

### PM2 Management Commands

```bash
# Start the application
pm2 start ecosystem.config.js

# Stop the application
pm2 stop Fluxion00API

# Restart the application
pm2 restart Fluxion00API

# View logs
pm2 logs Fluxion00API

# View status
pm2 status

# Monitor in real-time
pm2 monit

# Save current process list (survives reboot)
pm2 save

# Setup auto-startup on server reboot
pm2 startup
```

---

## Nginx Reverse Proxy

### Full Nginx Configuration

```
server {
    server_name fluxion.nn10dev.dashanddata.com;
    client_max_body_size 10G;

    # WebSocket endpoint
    location /ws/ {
        proxy_pass http://192.168.100.192:8005;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }

    # Main API + frontend
    location / {
        proxy_pass http://192.168.100.192:8005;

        proxy_http_version 1.1;
        proxy_set_header Connection "";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 600s;
    }

    # Static files (optional passthrough)
    location /static {
        proxy_pass http://192.168.100.192:8005/static;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 600s;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/fluxion.nn10dev.dashanddata.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/fluxion.nn10dev.dashanddata.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    if ($host = fluxion.nn10dev.dashanddata.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    server_name fluxion.nn10dev.dashanddata.com;
    return 404; # managed by Certbot
}
```

### Configuration Breakdown

#### WebSocket-Specific Headers (`location /ws/`)

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

**Why these are critical**:

- WebSocket protocol requires HTTP/1.1
- `Upgrade` header signals WebSocket handshake
- `Connection: upgrade` maintains persistent connection
- Without these, WebSocket connections fail with 400 errors

#### Timeout Configuration

```nginx
proxy_read_timeout 600s;
proxy_send_timeout 600s;
```

**Why 10 minutes (600s)**:

- Agent processing can take time (LLM calls, database queries)
- WebSocket connections are long-lived
- Prevents premature connection termination during long operations
- Default nginx timeout (60s) is too short for AI agent workflows

#### Proxy Headers

```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

**Purpose**:

- **Host**: Preserves original hostname (important for CORS)
- **X-Real-IP**: Client's actual IP address
- **X-Forwarded-For**: Full proxy chain (useful for logging)
- **X-Forwarded-Proto**: Original scheme (http/https) for redirect logic

#### Large File Support

```nginx
client_max_body_size 10G;
```

**Purpose**:

- Allows large file uploads (future document ingestion)
- Default is 1MB (too small for production use)
- Set high for flexibility

---

## SSL/TLS Configuration

### Certbot (Let's Encrypt)

The SSL certificates are managed by Certbot:

```nginx
ssl_certificate /etc/letsencrypt/live/fluxion.nn10dev.dashanddata.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/fluxion.nn10dev.dashanddata.com/privkey.pem;
include /etc/letsencrypt/options-ssl-nginx.conf;
ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
```

**Certificate renewal** (automatic):

```bash
# Certbot auto-renewal (runs via cron/systemd)
certbot renew

# Test renewal
certbot renew --dry-run
```

### HTTP to HTTPS Redirect

```nginx
server {
    if ($host = fluxion.nn10dev.dashanddata.com) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    server_name fluxion.nn10dev.dashanddata.com;
    return 404;
}
```

**How it works**:

- All HTTP traffic (port 80) is redirected to HTTPS (port 443)
- 301 = permanent redirect (browsers will cache this)
- Ensures all connections are encrypted

---

## Development vs Production

### Quick Comparison

| Aspect              | Development                  | Production                      |
| ------------------- | ---------------------------- | ------------------------------- |
| **Startup**         | `python run.py`              | `pm2 start ecosystem.config.js` |
| **.env Loading**    | run.py + src/**init**.py     | src/**init**.py only            |
| **Uvicorn**         | Python API (`uvicorn.run()`) | Direct binary invocation        |
| **Workers**         | 1 (single process)           | 3 (multi-process)               |
| **Auto-reload**     | Yes (`reload=True`)          | No (stability)                  |
| **Port**            | 8000                         | 8005                            |
| **Public Access**   | Direct (localhost)           | Via nginx reverse proxy         |
| **SSL/TLS**         | No                           | Yes (Let's Encrypt)             |
| **Process Manager** | Manual (Ctrl+C to stop)      | PM2 (auto-restart, monitoring)  |
| **Logs**            | Console output               | PM2 logs (`pm2 logs`)           |

### Environment Path Differences

**Development**:

```bash
# macOS paths
Project: /Users/nick/Documents/Fluxion00API
Virtualenv: /Users/nick/Documents/_environments/fluxion
Database: /Users/nick/Documents/_databases/NewsNexus10/newsnexus10.db
```

**Production**:

```bash
# Linux server paths
Project: /home/nick/applications/Fluxion00API
Virtualenv: /home/nick/environments/fluxion
Database: /home/nick/databases/NewsNexus10/newsnexus10.db
```

These paths are configured in the `.env` file and are environment-specific.

---

## Troubleshooting

### .env Not Loading

**Symptoms**: Database connection errors, missing API keys

**Solutions**:

1. Verify .env file exists in project root
2. Check PM2 `cwd` points to project root
3. Verify `src/__init__.py` has dotenv loading code
4. Check file permissions (must be readable by app user)

### WebSocket Connection Failures

**Symptoms**: Chat interface can't connect, 400/500 errors

**Solutions**:

1. Verify nginx WebSocket headers are configured
2. Check uvicorn is listening on correct port
3. Verify firewall allows port 8005 (internal)
4. Check nginx error logs: `sudo tail -f /var/log/nginx/error.log`

### PM2 Process Crashes

**Symptoms**: Application stops unexpectedly

**Solutions**:

1. Check PM2 logs: `pm2 logs Fluxion00API --lines 100`
2. Verify virtualenv path is correct
3. Check Python dependencies are installed
4. Look for unhandled exceptions in application code

### High Memory Usage

**Symptoms**: Server slowdowns, OOM errors

**Solutions**:

1. Reduce worker count in ecosystem.config.js
2. Monitor per-worker memory: `pm2 monit`
3. Check for memory leaks in agent/LLM code
4. Consider worker restart strategy: `pm2 restart Fluxion00API`

---

## Deployment Checklist

- [ ] .env file created in project root with production values
- [ ] Virtualenv activated and dependencies installed
- [ ] Database accessible from production server
- [ ] PM2 ecosystem.config.js configured with correct paths
- [ ] Nginx configuration installed and tested
- [ ] SSL certificate obtained via Certbot
- [ ] Firewall rules configured (allow 80, 443; internal 8005)
- [ ] PM2 startup script enabled: `pm2 startup` and `pm2 save`
- [ ] Application tested via public URL
- [ ] WebSocket connection tested
- [ ] Monitoring/alerting configured
- [ ] Backup strategy for .env file (store securely, not in git)

---

## Additional Resources

- [PM2 Documentation](https://pm2.keymetrics.io/docs/usage/quick-start/)
- [Uvicorn Deployment Guide](https://www.uvicorn.org/deployment/)
- [Nginx WebSocket Proxying](http://nginx.org/en/docs/http/websocket.html)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Let's Encrypt / Certbot](https://certbot.eff.org/)
