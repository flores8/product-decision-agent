import os
from pathlib import Path

# Weave configuration
WEAVE_PROJECT = "company-of-agents/tyler"

# API configuration
API_HOST = "0.0.0.0"
API_PORT = 3000 

# Default locations
DEFAULT_DATA_DIR = os.path.expanduser("~/.tyler")
DEFAULT_DB_PATH = os.path.join(DEFAULT_DATA_DIR, "tyler.db")

# Create default directory if it doesn't exist
os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)

# Database configuration
DATABASE_URL = os.getenv("TYLER_DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

# Other configurations can go here
MODEL_NAME = os.getenv("TYLER_MODEL_NAME", "gpt-4")
TEMPERATURE = float(os.getenv("TYLER_TEMPERATURE", "0.7")) 