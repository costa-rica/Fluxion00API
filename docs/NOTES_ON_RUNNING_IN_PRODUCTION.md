# Notes for running in production

## PM2 ecosystem.config.js

```js
    {
      name: "Fluxion00API",
      script: "/home/nick/environments/fluxion/bin/uvicorn",
      args: "src.api.app:app --host 0.0.0.0 --port 8005 --workers 3",
      cwd: "/home/nick/applications/Fluxion00API/",
      interpreter: "/home/nick/environments/fluxion/bin/python3",
      env: {
        PORT: 8005, // The port the app will listen on
        NAME_APP: "Fluxion00API",
        PATH_TO_DATABASE: "/home/nick/databases/NewsNexus10/",
        NAME_DB: "newsnexus10.db",
        PATH_TO_PYTHON_VENV: "/home/nick/environments/fluxion",
        PATH_TO_DOCUMENTS:
          "/home/nick/project_resources/Fluxion00API/docs_for_agent",
        URL_BASE_OLLAMA: "https://fell-st-ollama.dashanddata.com",
        KEY_OLLAMA: "SECRET_KEY",
        URL_BASE_OPENAI: "https://api.openai.com/v1",
        KEY_OPENAI: "SECRET_KEY",
      },
    },
```

## Nginx

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
