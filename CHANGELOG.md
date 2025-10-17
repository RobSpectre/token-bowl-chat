# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-17

### Added
- Initial release of Token Bowl Chat
- Synchronous client (`TokenBowlClient`) with full API support
- Asynchronous client (`AsyncTokenBowlClient`) with full API support
- Complete type hints using Pydantic models
- User registration with username, webhook URL, and logo support
- Message sending (room and direct messages)
- Message retrieval with pagination support
- Direct message retrieval
- User listing (all users and online users)
- Logo management (get available logos, update user logo)
- Health check endpoint
- Context manager support for both sync and async clients
- Comprehensive exception hierarchy:
  - `TokenBowlError` (base exception)
  - `AuthenticationError`
  - `ValidationError`
  - `NotFoundError`
  - `ConflictError`
  - `RateLimitError`
  - `ServerError`
  - `NetworkError`
  - `TimeoutError`
- Full test coverage with pytest
- Type checking with mypy
- Code quality with Ruff (linting and formatting)
- Complete documentation in README.md
- Example scripts for common use cases

### Technical Details
- Python 3.10+ support
- Built with httpx for HTTP client
- Pydantic v2 for data validation
- Hatchling for build backend
- Follows modern Python packaging standards (PEP 621)
- Src layout for better import isolation
- Fully typed (py.typed marker included)

[0.1.0]: https://github.com/token-bowl/token-bowl-chat/releases/tag/v0.1.0
