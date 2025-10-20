# Contributing to Token Bowl Chat

Thank you for your interest in contributing to Token Bowl Chat! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/token-bowl-chat.git
   cd token-bowl-chat
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/RobSpectre/token-bowl-chat.git
   ```

## Development Setup

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is the fastest Python package installer and is recommended for development:

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in editable mode with dev dependencies
uv pip install -e ".[dev]"
```

### Using pip

Alternatively, you can use traditional pip:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in editable mode with dev dependencies
pip install -e ".[dev]"
```

## Making Changes

### Branching Strategy

1. **Keep your main branch in sync** with upstream:
   ```bash
   git checkout main
   git pull upstream main
   ```

2. **Create a feature branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

   Use descriptive branch names:
   - `feature/` - New features
   - `fix/` - Bug fixes
   - `docs/` - Documentation changes
   - `refactor/` - Code refactoring
   - `test/` - Test additions or modifications

### Code Style

This project follows Python best practices:

- **Type hints**: All functions should have complete type annotations
- **Docstrings**: Use clear docstrings for all public APIs (Google style)
- **Line length**: Maximum 88 characters (enforced by ruff)
- **Imports**: Organized and sorted automatically by ruff

### Writing Code

1. **Keep changes focused**: Each pull request should address a single concern
2. **Write tests**: All new features should include tests
3. **Update documentation**: Update relevant documentation for your changes
4. **Add type hints**: Ensure all new code has proper type annotations

## Testing

### Running Tests

Run the full test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=token_bowl_chat --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run specific test
pytest tests/test_client.py::test_send_message_room
```

### Test Requirements

- **Coverage**: Aim for >80% code coverage for new code
- **All test types**: Include unit tests and integration tests where appropriate
- **Async tests**: Use `@pytest.mark.asyncio` for async client tests
- **Mocking**: Use `pytest-httpx` for mocking HTTP requests

### Writing Tests

Example test structure:

```python
import pytest
from pytest_httpx import HTTPXMock
from token_bowl_chat import TokenBowlClient

def test_your_feature(httpx_mock: HTTPXMock) -> None:
    """Test description explaining what is being tested."""
    # Arrange
    client = TokenBowlClient(api_key="test-key", base_url="http://test.example.com")
    httpx_mock.add_response(
        method="POST",
        url="http://test.example.com/endpoint",
        json={"result": "success"},
        status_code=200,
    )

    # Act
    result = client.your_method()

    # Assert
    assert result.some_field == "expected_value"
```

## Code Quality

### Linting and Formatting

This project uses ruff for linting and formatting:

```bash
# Check code quality
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Type Checking

Use mypy for static type checking:

```bash
mypy src
```

### Pre-commit Checks

Before committing, ensure:

1. ✅ All tests pass: `pytest`
2. ✅ No linting errors: `ruff check .`
3. ✅ Code is formatted: `ruff format .`
4. ✅ Type checking passes: `mypy src`

You can run all checks at once using the Makefile:

```bash
make ci
```

Or run them manually:

```bash
pytest && ruff check . && ruff format . && mypy src
```

### Automated Pre-commit Hooks (Recommended)

To automatically run all CI checks before each commit, install the pre-commit hooks:

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the git hooks
pre-commit install
```

Now the following checks will run automatically before each commit:
- ✅ **Ruff formatting** - Auto-formats your code
- ✅ **Ruff linting** - Checks and fixes linting issues
- ✅ **Mypy type checking** - Validates type annotations
- ✅ **Pytest** - Runs all tests

If any check fails, the commit will be blocked until you fix the issues.

**Manual run:**
To manually run pre-commit on all files:
```bash
pre-commit run --all-files
```

**Skip hooks (emergency only):**
If you need to commit without running hooks (not recommended):
```bash
git commit --no-verify -m "Your message"
```

## Submitting Changes

### Commit Messages

Write clear, descriptive commit messages:

```
Add feature to handle message pagination

- Implement offset-based pagination in get_messages()
- Add pagination metadata to response models
- Include tests for pagination edge cases

Fixes #123
```

### Pull Request Process

1. **Update your branch** with the latest upstream changes:
   ```bash
   git checkout main
   git pull upstream main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Push your changes** to your fork:
   ```bash
   git push origin your-feature-branch
   ```

3. **Open a Pull Request** on GitHub with:
   - Clear title describing the change
   - Detailed description of what and why
   - Reference to related issues (e.g., "Fixes #123")
   - Screenshots for UI changes (if applicable)

4. **Address review feedback** promptly and professionally

5. **Ensure CI passes**: All automated checks must pass before merge

### Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated (if applicable)
- [ ] Type hints added to all new functions
- [ ] CHANGELOG.md updated (for notable changes)
- [ ] Commit messages are clear and descriptive

## Reporting Issues

### Bug Reports

When reporting bugs, include:

1. **Description**: Clear description of the issue
2. **Reproduction steps**: Minimal code to reproduce the problem
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**:
   - Python version
   - Package version
   - Operating system
   - Relevant dependencies

Example:

```markdown
**Description**
Client raises TimeoutError when sending large messages

**Reproduction**
```python
from token_bowl_chat import TokenBowlClient

client = TokenBowlClient(api_key="...")
client.send_message("x" * 10000)  # Raises TimeoutError
```

**Expected**: Message sent successfully
**Actual**: TimeoutError raised

**Environment**
- Python 3.11.5
- token-bowl-chat 0.1.1
- Ubuntu 22.04
```

### Feature Requests

When requesting features, include:

1. **Use case**: What problem does this solve?
2. **Proposed solution**: How might this work?
3. **Alternatives**: Other approaches you've considered
4. **Additional context**: Any other relevant information

## Questions?

If you have questions about contributing, feel free to:

- Open a discussion on GitHub
- Comment on an existing issue
- Reach out to the maintainers

Thank you for contributing to Token Bowl Chat! 🎉
