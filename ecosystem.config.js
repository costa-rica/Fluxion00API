/**
 * PM2 Configuration for Fluxion00API
 *
 * This configuration ensures that environment variables from .env are properly loaded.
 *
 * IMPORTANT: This config runs Python with run.py, which loads the .env file BEFORE
 * starting uvicorn. DO NOT run uvicorn directly or environment variables will not load.
 *
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 restart Fluxion00API
 *   pm2 logs Fluxion00API
 *   pm2 stop Fluxion00API
 */

module.exports = {
  apps: [
    {
      name: 'Fluxion00API',

      // Run Python with run.py (NOT uvicorn directly)
      script: 'run.py',
      interpreter: '/home/nick/environments/fluxion/bin/python3',

      // Working directory (where .env file is located)
      cwd: '/home/nick/applications/Fluxion00API',

      // Environment variables (optional overrides)
      env: {
        PORT: '8005',
        HOST: '0.0.0.0',
        RELOAD: 'false',  // Disable reload in production
      },

      // PM2 runtime options
      instances: 1,  // Single instance (FastAPI handles concurrency with workers)
      exec_mode: 'fork',  // Use fork mode for Python
      autorestart: true,
      watch: false,  // Don't watch files in production
      max_memory_restart: '500M',

      // Logging
      error_file: '/home/nick/logs/fluxion00api-error.log',
      out_file: '/home/nick/logs/fluxion00api-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

      // Merge logs from all instances
      merge_logs: true,

      // Time in ms before forcing a reload
      kill_timeout: 5000,
    }
  ]
};
