import os
from typing import Dict, Any
from urllib.parse import quote_plus

def get_database_url() -> str:
    """
    Get the database URL from environment variables or return default PostgreSQL URL.
    """
    db_type = os.getenv("TYLER_DB_TYPE", "postgresql")
    
    if db_type == "postgresql":
        host = os.getenv("TYLER_DB_HOST", "localhost")
        port = os.getenv("TYLER_DB_PORT", "5432")
        database = os.getenv("TYLER_DB_NAME", "tyler")
        user = os.getenv("TYLER_DB_USER", "tyler")
        password = os.getenv("TYLER_DB_PASSWORD", "tyler_dev")
        
        return f"postgresql://{user}:{quote_plus(password)}@{host}:{port}/{database}"
    
    elif db_type == "sqlite":
        # Fallback to SQLite for testing or simple deployments
        data_dir = os.path.expanduser("~/.tyler/data")
        os.makedirs(data_dir, exist_ok=True)
        return f"sqlite:///{data_dir}/tyler.db"
    
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def get_database_config() -> Dict[str, Any]:
    """
    Get the SQLAlchemy configuration dictionary.
    """
    return {
        "url": get_database_url(),
        "echo": os.getenv("TYLER_DB_ECHO", "false").lower() == "true",
        "pool_size": int(os.getenv("TYLER_DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("TYLER_DB_MAX_OVERFLOW", "10")),
        "pool_timeout": int(os.getenv("TYLER_DB_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("TYLER_DB_POOL_RECYCLE", "1800")),
    } 