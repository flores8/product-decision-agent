---
sidebar_position: 3
---

# Configuration Guide

Tyler offers extensive configuration options to customize its behavior for your specific needs. This guide covers all available configuration options and their usage.

## Environment Variables

Tyler uses environment variables for configuration. These can be set in a `.env` file or directly in your environment.

### Core Settings

```bash
# LLM Provider Configuration
OPENAI_API_KEY=your-openai-api-key
# Or for other providers:
ANTHROPIC_API_KEY=your-anthropic-key
AZURE_API_KEY=your-azure-key
VERTEX_PROJECT=your-project-id

# Database Configuration
TYLER_DB_TYPE=postgresql  # or sqlite
TYLER_DB_HOST=localhost
TYLER_DB_PORT=5432
TYLER_DB_NAME=tyler
TYLER_DB_USER=tyler
TYLER_DB_PASSWORD=tyler_dev

# File Storage Configuration
TYLER_FILE_STORAGE_TYPE=local  # or s3
TYLER_FILE_STORAGE_PATH=/path/to/files

# Logging Configuration
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
WANDB_API_KEY=your-wandb-api-key  # For Weave monitoring
```

### Optional Settings

```bash
# Database Pool Settings
TYLER_DB_ECHO=false
TYLER_DB_POOL_SIZE=5
TYLER_DB_MAX_OVERFLOW=10
TYLER_DB_POOL_TIMEOUT=30
TYLER_DB_POOL_RECYCLE=1800

# Service Integration Settings
NOTION_TOKEN=your-notion-token
SLACK_BOT_TOKEN=your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
```

## Agent Configuration

The `Agent` class accepts various configuration options to customize its behavior:

```python
from tyler.models.agent import Agent

agent = Agent(
    # Required
    model_name="gpt-4o",  # LLM model to use
    purpose="To help with tasks",  # Agent's purpose
    
    # Optional
    temperature=0.7,  # Response creativity (0.0-1.0)
    max_tokens=1000,  # Maximum response length
    tools=[],  # List of custom tools
    system_prompt="Custom system prompt",  # Override default prompt
    attributes={},  # Custom metadata
)
```

### Available Models

Tyler supports any model available through LiteLLM:

```python
# OpenAI
agent = Agent(model_name="gpt-4o")

# Anthropic
agent = Agent(model_name="claude-2")

# Azure OpenAI
agent = Agent(model_name="azure/your-deployment-name")

# Google VertexAI
agent = Agent(model_name="chat-bison")

# AWS Bedrock
agent = Agent(model_name="anthropic.claude-v2")
```

## Storage Configuration

### Database Options

#### PostgreSQL
```python
from tyler.database import Database

db = Database(
    db_type="postgresql",
    host="localhost",
    port=5432,
    database="tyler",
    user="tyler",
    password="tyler_dev"
)
```

#### SQLite
```python
from tyler.database import Database

db = Database(
    db_type="sqlite",
    sqlite_path="~/.tyler/data/tyler.db"
)
```

### File Storage Options

#### Local Storage
```python
from tyler.storage import FileStorage

storage = FileStorage(
    storage_type="local",
    base_path="/path/to/files"
)
```

#### S3 Storage
```python
from tyler.storage import FileStorage

storage = FileStorage(
    storage_type="s3",
    bucket_name="your-bucket",
    aws_access_key_id="your-access-key",
    aws_secret_access_key="your-secret-key",
    region_name="us-west-2"
)
```

## Monitoring Configuration

### Weave Integration
```python
from tyler.monitoring import WeaveMonitor

monitor = WeaveMonitor(
    api_key="your-wandb-api-key",
    project_name="tyler-monitoring",
    entity="your-username"
)
```

## Service Integrations

### Slack Configuration
```python
from tyler.integrations.slack import SlackIntegration

slack = SlackIntegration(
    bot_token="your-bot-token",
    signing_secret="your-signing-secret",
    default_channel="general"
)
```

### Notion Configuration
```python
from tyler.integrations.notion import NotionIntegration

notion = NotionIntegration(
    token="your-notion-token",
    default_page_id="your-default-page-id"
)
```

## Custom Tool Configuration

Create custom tools by defining their schema and implementation:

```python
weather_tool = {
    "definition": {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and country"
                    }
                },
                "required": ["location"]
            }
        }
    },
    "implementation": lambda location: f"Weather in {location}: Sunny",
    "attributes": {
        "type": "standard"  # or "interrupt" for interrupt tools
    }
}

agent = Agent(
    model_name="gpt-4o",
    purpose="Weather assistant",
    tools=[weather_tool]
)
```

## Best Practices

1. **Environment Variables**
   - Use `.env` files for local development
   - Use secure secrets management in production
   - Never commit sensitive values to version control

2. **Database Configuration**
   - Use connection pooling for better performance
   - Set appropriate timeouts and pool sizes
   - Use SSL in production

3. **File Storage**
   - Set appropriate file size limits
   - Use secure storage in production
   - Implement proper backup strategies

4. **Monitoring**
   - Enable monitoring in production
   - Set appropriate logging levels
   - Monitor token usage and costs

5. **Security**
   - Use HTTPS for all external connections
   - Implement rate limiting
   - Follow the principle of least privilege

## Troubleshooting

### Common Configuration Issues

1. **Database Connection Failures**
   ```python
   # Check connection
   from tyler.database import Database
   db = Database()
   await db.test_connection()
   ```

2. **File Storage Issues**
   ```python
   # Verify storage access
   from tyler.storage import FileStorage
   storage = FileStorage()
   await storage.test_access()
   ```

3. **API Authentication Issues**
   ```python
   # Test API key
   from tyler.utils import test_api_key
   is_valid = await test_api_key()
   ```

## Next Steps

- Learn about [Core Concepts](./core-concepts.md)
- Explore [API Reference](./category/api-reference)
- See [Examples](./category/examples) for common configurations

**SQLite Setup (no Docker needed):**
```bash
# Install Tyler with SQLite dependencies
pip install tyler-agent

# Initialize SQLite database
# Uses default location (~/.tyler/data/tyler.db)
python -m tyler.database.cli init --db-type sqlite

# Or specify custom location:
python -m tyler.database.cli init --db-type sqlite --sqlite-path ./my_database.db
``` 