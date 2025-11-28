"""
Fluxion00API - Main package initialization.

IMPORTANT: This module loads environment variables from .env file
BEFORE any other modules are imported. This ensures that database
connections and other components have access to configuration.
"""

import os
from pathlib import Path

# Load environment variables from .env file
# This MUST happen before any other src modules are imported
try:
    from dotenv import load_dotenv

    # Find .env file in project root (parent of src/)
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"

    if env_file.exists():
        load_dotenv(dotenv_path=env_file, override=True)
    else:
        # If .env doesn't exist, try to load from current directory
        load_dotenv(override=True)

except ImportError:
    # python-dotenv not installed - environment variables must come from system
    pass
