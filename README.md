# Tyler

Tyler is an AI chat assistant built with Streamlit and powered by GPT-4. It can converse with users, answer questions, and create plans to perform tasks.

## Prerequisites

- Python 3.12.8
- pyenv (for Python version management)
- pip (Python package manager)

## Development Setup

1. **Install pyenv** (if not already installed)

   ```bash
   curl https://pyenv.run | bash
   ```

   Add to your shell configuration file (~/.bashrc, ~/.zshrc, etc.):
   ```bash
   export PATH="$HOME/.pyenv/bin:$PATH"
   eval "$(pyenv init -)"
   eval "$(pyenv virtualenv-init -)"
   ```

2. **Install Python 3.12.8 with pyenv**
   ```bash
   pyenv install 3.12.8
   ```

3. **Create a virtual environment**
   ```bash
   # Create and activate a new virtual environment for Tyler
   pyenv virtualenv 3.12.8 tyler-env
   pyenv local tyler-env
   ```

4. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tyler.git
   cd tyler
   ```

5. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

6. **Set up secrets**
   
   Create a `.streamlit/secrets.toml` file:
   ```toml
   OPENAI_API_KEY = "your-openai-api-key"
   NOTION_TOKEN = "your-notion-token"  # Optional: Only if using Notion integration
   WANDB_API_KEY = "your-wandb-api-key"  # Optional: Only if using Weights & Biases
   ```

   Note: Make sure to add `.streamlit/secrets.toml` to your `.gitignore` file to keep your secrets secure.

7. **Run the application**
   ```bash
   streamlit run app.py
   ```

   The application will be available at `http://localhost:8501`

## Project Structure

```
tyler/
├── app.py                 # Main Streamlit application
├── models/
│   └── Tyler.py          # Tyler model implementation
├── prompts/
│   └── Tyler.py          # Prompt templates and configurations
├── tools/                 # Tool implementations
│   ├── command_line.py
│   └── notion.py
├── utils/                 # Utility functions
│   ├── helpers.py
│   └── tool_runner.py
└── tests/                 # Test suite
```

## Running Tests

```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


