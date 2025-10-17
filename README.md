# Token Bowl Chat Client

A chat client for Token Bowl.

## Features

- Modern Python package structure (src layout)
- Type-safe with MyPy
- Linted and formatted with Ruff
- Tested with Pytest
- Configured with pyproject.toml (PEP 621)

## Installation

### For development

```bash
# Clone the repository
git clone https://github.com/yourusername/token-bowl-chat-client.git
cd token-bowl-chat-client

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### For users

```bash
pip install token-bowl-chat-client
```

## Usage

```python
from token_bowl_chat_client import example_function

# Your code here
```

## Development

### Running tests

```bash
pytest
```

### Running tests with coverage

```bash
pytest --cov=token_bowl_chat_client --cov-report=html
```

### Linting and formatting

```bash
# Check code quality
ruff check .

# Format code
ruff format .

# Type checking
mypy src
```

### Auto-fix issues

```bash
# Fix auto-fixable linting issues
ruff check --fix .
```

## Project Structure

```
token-bowl-chat-client/
├── src/
│   └── token_bowl_chat_client/
│       ├── __init__.py
│       └── py.typed
├── tests/
│   └── __init__.py
├── docs/
├── pyproject.toml
├── README.md
├── LICENSE
└── .gitignore
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
