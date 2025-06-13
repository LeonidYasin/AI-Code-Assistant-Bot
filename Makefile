.PHONY: help install test lint format clean

# Variables
PYTHON = python
PIP = pip
PYTEST = pytest
FLAKE8 = flake8
BLACK = black
ISORT = isort
MYPY = mypy

# Default target
help:
	@echo "Available targets:"
	@echo "  install    - Install development dependencies"
	@echo "  test       - Run tests"
	@echo "  lint       - Check code style with flake8 and black"
	@echo "  format     - Format code with black and isort"
	@echo "  typecheck  - Run static type checking with mypy"
	@echo "  check      - Run all checks (lint, typecheck, test)"
	@echo "  clean      - Remove build artifacts and cache"

# Install development dependencies
install:
	$(PIP) install -r requirements-dev.txt
	pre-commit install

# Run tests
test:
	$(PYTEST) tests/ -v --cov=ai_code_assistant --cov-report=term-missing

# Check code style
lint:
	$(FLAKE8 ai_code_assistant tests
	$(BLACK) --check ai_code_assistant tests

# Format code
format:
	$(BLACK) ai_code_assistant tests
	$(ISORT) ai_code_assistant tests

# Run static type checking
typecheck:
	$(MYPY) ai_code_assistant

# Run all checks
check: lint typecheck test

# Clean up
clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .mypy_cache/
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.py[co]" -delete
	find . -type f -name "*~" -delete

# Alias for check
dev: check
