.PHONY: help lint format-check type-check test ci clean install pre-commit-install

# Default target - show help
help:
	@echo "Available targets:"
	@echo "  make ci                  - Run all CI checks (lint, type-check, test)"
	@echo "  make lint                - Run ruff linting checks"
	@echo "  make format-check        - Check code formatting with ruff"
	@echo "  make format              - Auto-format code with ruff"
	@echo "  make type-check          - Run mypy type checking"
	@echo "  make test                - Run pytest with coverage"
	@echo "  make install             - Install package with dev dependencies"
	@echo "  make pre-commit-install  - Install pre-commit hooks"
	@echo "  make clean               - Remove build artifacts and caches"

# Install dependencies (same as CI)
install:
	python -m pip install --upgrade pip
	pip install -e .[dev]

# Lint and format check (mirrors CI lint job)
format-check:
	@echo "==> Checking code formatting..."
	ruff format --check .

lint:
	@echo "==> Running linter..."
	ruff check .

# Type check (mirrors CI type-check job)
type-check:
	@echo "==> Running type checker..."
	mypy src

# Test (mirrors CI test job)
test:
	@echo "==> Running tests with coverage..."
	pytest

# Auto-format code (not in CI, but useful for local development)
format:
	@echo "==> Auto-formatting code..."
	ruff format .
	@echo "==> Auto-fixing lint issues..."
	ruff check --fix .

# Run all CI checks locally (same order as CI)
ci: format-check lint type-check test
	@echo ""
	@echo "✓ All CI checks passed!"

# Install pre-commit hooks
pre-commit-install:
	@echo "==> Installing pre-commit hooks..."
	pre-commit install
	@echo "✓ Pre-commit hooks installed!"
	@echo ""
	@echo "The following checks will now run automatically before each commit:"
	@echo "  - Ruff formatting"
	@echo "  - Ruff linting"
	@echo "  - Mypy type checking"
	@echo "  - Pytest"
	@echo ""
	@echo "To run manually: pre-commit run --all-files"

# Clean build artifacts
clean:
	@echo "==> Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned!"
