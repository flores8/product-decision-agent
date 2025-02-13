from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tyler",
    version="0.1.4",
    author="adamwdraper",
    description="Tyler: A framework for AI agents with a complete lack of conventional limitations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(include=["tyler", "tyler.*"]),
    include_package_data=True,
    python_requires=">=3.12",
    install_requires=[
        # Core LLM dependencies
        "litellm>=1.60.2",
        "openai>=1.61.0",
        "tiktoken>=0.8.0",
        
        # File processing
        "pdf2image>=1.17.0",
        "PyPDF2>=3.0.1",
        "python-magic>=0.4.0",  # Requires libmagic system dependency
        "pillow>=11.0.0",
        
        # Database dependencies
        "SQLAlchemy>=2.0.36",
        "greenlet>=3.1.1",  # Required for SQLAlchemy async operations
        "alembic>=1.14.1",
        "asyncpg>=0.30.0",  # PostgreSQL support
        "aiosqlite>=0.21.0",  # SQLite support
        "psycopg2-binary>=2.9.9",  # For CLI tools
        
        # HTTP and networking
        "aiohttp>=3.11.11",
        "httpx>=0.27.2",
        "requests>=2.32.3",
        "beautifulsoup4>=4.12.0",  # Add this for web tools HTML parsing
        
        # Utilities
        "python-dotenv>=1.0.1",
        "click>=8.1.8",
        "pydantic>=2.10.4",
        "backoff>=2.2.1",
        "uuid_utils>=0.10.0",
        
        # Monitoring and metrics
        "weave>=0.51.32",
        "wandb>=0.19.1",
        
        # Optional integrations
        "slack_sdk>=3.34.0",  # Slack support
        "huggingface-hub>=0.27.0",  # HuggingFace support
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.4",
            "pytest-asyncio>=0.25.2",
            "pytest-cov>=6.0.0",
            "coverage>=7.6.10",
            "pip-tools>=7.4.1",
            "pipdeptree>=2.25.0",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "License :: Free for non-commercial use",  # Changed to non-commercial use
    ],
    entry_points={
        "console_scripts": [
            "tyler-db=tyler.database.cli:main",
        ],
    },
    package_data={
        "tyler": [
            "database/migrations/alembic.ini",
            "database/migrations/script.py.mako",
            "database/migrations/env.py",
            "database/migrations/versions/*.py",
            "tools/*.py",  # Include all tool modules
            "tools/**/*.py",  # Include any nested tool modules
        ],
    },
    url="https://github.com/adamwdraper/tyler",
    project_urls={
        "Bug Tracker": "https://github.com/adamwdraper/tyler/issues",
        "Documentation": "https://github.com/adamwdraper/tyler#readme",
        "Source Code": "https://github.com/adamwdraper/tyler",
    },
) 