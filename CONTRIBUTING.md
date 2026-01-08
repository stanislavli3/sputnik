# Contributing to Sputnik

Thank you for your interest in contributing to Sputnik! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Git

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/sputnik.git
cd sputnik

# Install dependencies
make install
# or manually:
# pip install -e ".[dev]"
# cd frontend && npm install

# Setup demo database
make db-setup
```

## Development Workflow

### Running the Application

```bash
# Start backend (Terminal 1)
make backend

# Start frontend (Terminal 2)
make frontend
```

Or use the Makefile:
```bash
make dev  # Shows instructions for running both
```

### Code Quality

Before committing, ensure your code passes:

```bash
# Lint
make lint

# Format
make format

# Type check
make typecheck

# Tests
make test
```

## Making Changes

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages

Follow conventional commits:
- `feat: add new SQL generator`
- `fix: resolve query validation issue`
- `docs: update API documentation`
- `refactor: simplify rollout collection`

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure all tests pass and code is linted
4. Update documentation if needed
5. Create a pull request with a clear description

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use `ruff` for linting and formatting

### TypeScript/React

- Follow ESLint rules
- Use TypeScript for all new code
- Use functional components with hooks
- Follow existing component patterns

## Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for good test coverage

```bash
# Run tests
make test

# Run with coverage
pytest --cov=sputnik --cov-report=html
```

## Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples for new features

## Questions?

Open an issue or start a discussion. We're happy to help!

