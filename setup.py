from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tyler",
    version="0.1.0",
    author="Dad",
    description="An AI chat assistant powered by GPT-4",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(include=["tyler", "tyler.*"]),
    python_requires=">=3.12",
    install_requires=[
        "aiohappyeyeballs>=2.4.4",
        "aiohttp>=3.11.11",
        "backoff>=2.2.1",
        "beautifulsoup4>=4.12.3",
        "emoji>=2.14.0",
        "httpx>=0.27.2",
        "huggingface-hub>=0.27.0",
        "litellm>=1.56.3",
        "narwhals>=1.19.1",
        "openai>=1.58.1",
        "pdf2image>=1.17.0",
        "pillow>=11.0.0",
        "pydantic>=2.10.4",
        "PyPDF2>=3.0.1",
        "python-dotenv>=1.0.1",
        "python-magic>=0.4.27",
        "requests>=2.32.3",
        "slack_sdk>=3.34.0",
        "SQLAlchemy>=2.0.36",
        "tiktoken>=0.8.0",
        "uuid_utils>=0.10.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.4",
            "pytest-cov>=6.0.0",
        ],
        "postgres": [
            "psycopg2-binary>=2.9.9",
        ],
        "mysql": [
            "mysqlclient>=2.2.4",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Private :: Do Not Upload",
    ],
) 