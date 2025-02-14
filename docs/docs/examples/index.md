---
sidebar_position: 1
---

# Examples

This section contains practical examples demonstrating how to use Tyler in various scenarios. Each example is designed to showcase different features and use cases.

## Quick Links

1. [Using Tools](./using-tools.md) - Learn how to use and create custom tools
2. [Full Configuration](./full-configuration.md) - Explore all configuration options
3. [Database Storage](./database-storage.md) - Set up persistent storage
4. [Interrupt Tools](./interrupt-tools.md) - Implement content moderation and control flow
5. [Message Attachments](./message-attachments.md) - Handle file attachments and processing

## Running the Examples

All examples are available in the [examples directory](https://github.com/adamwdraper/tyler/tree/main/examples) of the Tyler repository.

To run any example:

1. Clone the repository:
```bash
git clone https://github.com/adamwdraper/tyler.git
cd tyler
```

2. Install dependencies:
```bash
pip install tyler-agent[dev]
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. Run an example:
```bash
python examples/2-using_tools.py
```

## Example Structure

Each example in this section includes:
- Complete source code
- Step-by-step explanation
- Key concepts covered
- Configuration requirements
- Expected output

## Prerequisites

Before running the examples, ensure you have:
- Python 3.12.8 or later
- Required system libraries (libmagic, poppler)
- API keys for services used (OpenAI, etc.)
- Database setup (if using PostgreSQL examples)

## Getting Help

If you encounter issues while running the examples:
1. Check the [Configuration Guide](../configuration.md)
2. Search [GitHub Issues](https://github.com/adamwdraper/tyler/issues)
3. Ask in [GitHub Discussions](https://github.com/adamwdraper/tyler/discussions) 