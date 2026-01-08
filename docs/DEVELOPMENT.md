# Development Guide

This guide covers development practices, architecture decisions, and common workflows for Sputnik.

## Project Structure

```
sputnik/
├── frontend/              # React/TypeScript frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/         # Page components
│   │   └── lib/          # Utilities
│   └── public/           # Static assets
├── src/sputnik/          # Python backend
│   ├── api/              # FastAPI server and routes
│   ├── agent/            # Agent modules (planner, SQL generator)
│   ├── distill/          # On-policy distillation
│   ├── env/              # ERP connectors
│   └── eval/             # Evaluation framework
├── scripts/              # Utility scripts
├── tests/                # Test suite
└── docs/                 # Documentation
```

## Development Commands

See `Makefile` for all available commands:

```bash
make help              # Show all commands
make install           # Install all dependencies
make setup             # Full setup (install + database)
make dev               # Start development (instructions)
make backend           # Start backend server
make frontend          # Start frontend server
make test              # Run tests
make lint              # Lint code
make format            # Format code
make typecheck         # Type check Python
make clean             # Clean build artifacts
```

## Architecture

### Backend (Python)

- **FastAPI**: REST API server
- **DuckDB**: Demo ERP database
- **Pydantic**: Data validation
- **On-policy distillation**: Learning framework

### Frontend (React/TypeScript)

- **Vite**: Build tool and dev server
- **React Router**: Routing
- **TanStack Query**: Data fetching
- **shadcn/ui**: UI components
- **Tailwind CSS**: Styling

## API Endpoints

- `GET /health` - Health check
- `GET /api/v1/schema` - Get ERP schema
- `POST /api/v1/query` - Execute natural language query
- `GET /api/v1/rollouts` - List rollouts
- `POST /api/v1/rollouts/train` - Train on rollouts

See http://localhost:8000/docs for full API documentation.

## Adding New Features

### Backend

1. Create feature module in `src/sputnik/`
2. Add API route in `src/sputnik/api/routes/`
3. Add tests in `tests/`
4. Update documentation

### Frontend

1. Create component in `frontend/src/components/`
2. Add page/route if needed
3. Add API client calls
4. Update types

## Testing

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_reverse_kl.py

# Run with coverage
pytest --cov=sputnik --cov-report=html
```

## Code Quality

### Python

- Use `ruff` for linting and formatting
- Use `mypy` for type checking
- Follow PEP 8

### TypeScript

- Use ESLint
- Use TypeScript strict mode
- Follow React best practices

## Database

The demo database is created with:

```bash
make db-setup
# or
python scripts/setup_demo_db.py
```

Database file: `demo_erp.duckdb` (gitignored)

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

## Troubleshooting

### Backend won't start

- Check Python dependencies: `pip list | grep fastapi`
- Check database exists: `ls demo_erp.duckdb`
- Check port 8000 is free: `lsof -i :8000`

### Frontend won't start

- Check Node version: `node --version` (should be 18+)
- Reinstall dependencies: `cd frontend && rm -rf node_modules && npm install`
- Check port 8080 is free: `lsof -i :8080`

### Import errors

- Ensure you're in the project root
- Check `src/` is in Python path
- Reinstall package: `pip install -e .`

## Performance

- Backend uses async FastAPI for performance
- Frontend uses Vite for fast HMR
- Database queries are optimized for read-only access

## Security

- All SQL queries are validated as read-only
- CORS is configured for development
- API keys should be in `.env` (gitignored)

## Deployment

See deployment documentation (to be added) for production setup.

