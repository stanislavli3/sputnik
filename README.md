# Sputnik

> **AI reliability layer for ERP analytics**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue.svg)](.github/workflows/ci.yml)

Sputnik is a reliability layer that enables safe, accurate AI reasoning on top of ERP data. It answers natural-language business questions over SQL-backed ERP systems and becomes more reliable over time by learning from real usage patterns.

## The Problem

Enterprise Resource Planning (ERP) systems contain critical business data—revenue, inventory, customer relationships, financial transactions. Yet this data is often locked behind complex interfaces that require specialized knowledge to query effectively. Business teams rely on data analysts and SQL experts to answer even simple questions, creating bottlenecks and delays.

Traditional AI solutions for ERP analytics face reliability challenges:
- **Hallucination**: Models generate plausible-sounding but incorrect SQL queries
- **Safety**: Risk of executing destructive operations on production data
- **Context**: Difficulty understanding complex ERP schemas and relationships
- **Adaptation**: Models don't improve from real-world usage patterns

## The Solution

Sputnik provides an **AI analyst** that:

1. **Answers questions naturally**: Ask business questions in plain English
2. **Verifies itself**: Validates SQL queries before execution, ensures read-only access
3. **Learns continuously**: Improves from real usage patterns via on-policy learning
4. **Stays safe**: Enforces read-only queries, audit logging, and access controls

Sputnik sits between your business users and your ERP data, providing a reliable, self-improving interface that becomes more accurate with each interaction.

## Architecture

```
┌─────────────┐
│   Business  │
│   Question  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Agent Planner  │  ← Breaks down question into steps
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQL Generator  │  ← Converts to validated SQL
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Verifier      │  ← Ensures read-only, safe queries
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ERP Connector  │  ← Executes queries (DuckDB, Odoo, etc.)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Learning Loop  │  ← Improves from usage patterns
└─────────────────┘
```

## Features

- **Natural Language Interface**: Ask questions in plain English
- **SQL Generation**: Automatically generates validated SQL queries
- **Read-Only Safety**: Enforces read-only queries by default
- **Schema Awareness**: Understands ERP table relationships and structure
- **Continuous Learning**: Improves from real usage via on-policy distillation
- **Multiple Connectors**: Supports DuckDB (demo), with plans for Odoo, NetSuite, SAP
- **Evaluation Framework**: Built-in metrics for accuracy and safety
- **Type-Safe**: Full type annotations with mypy validation

## Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/sputnik.git
cd sputnik

# Install dependencies (using uv or poetry)
uv pip install -e ".[dev]"
# or
poetry install
```

### Setup Demo Database

```bash
python scripts/setup_demo_db.py
```

This creates a demo ERP database with sample tables: `customers`, `orders`, `invoices`, `inventory_movements`.

### Run Interactive Demo

```bash
python scripts/run_demo.py
```

Example questions:
- "What is the total revenue?"
- "How many customers do we have?"
- "What is our inventory status?"

### Run Evaluation

```bash
python scripts/run_eval.py
```

### Run Distillation Training

```bash
python scripts/run_on_policy_distill.py
```

## Demo

> **Note**: Demo GIF/image placeholder. In production, this would show:
> - Interactive question answering
> - SQL query generation
> - Results visualization
> - Learning metrics over time

## Roadmap

### Phase 1: Foundation (Current)
- [x] Core architecture and types
- [x] DuckDB connector
- [x] Basic SQL generation
- [x] On-policy distillation skeleton
- [x] Evaluation framework

### Phase 2: Production Readiness
- [ ] Real LLM integration (replace mocks)
- [ ] Odoo connector
- [ ] NetSuite connector
- [ ] Comprehensive test suite
- [ ] Performance optimization

### Phase 3: Enterprise Features
- [ ] Audit logging
- [ ] Access control (allowlist/denylist)
- [ ] PII detection and handling
- [ ] Multi-tenant support
- [ ] Dashboard and monitoring

### Phase 4: Advanced Learning
- [ ] Fine-tuning pipeline
- [ ] Active learning
- [ ] Human feedback integration
- [ ] Model versioning and rollback

## Security & Safety

Sputnik is designed with safety as a first-class concern:

- **Read-Only by Default**: All queries are validated to be read-only
- **Query Validation**: SQL queries are checked before execution
- **Audit Logging**: All queries and responses are logged (roadmap)
- **Access Control**: Table and column-level access control (roadmap)
- **PII Handling**: Detection and masking of personally identifiable information (roadmap)

See [docs/SAFETY.md](docs/SAFETY.md) for detailed safety documentation.

## FAQ

### What ERP systems does Sputnik support?

Currently, Sputnik includes a DuckDB connector for demos and testing. We're planning connectors for:
- Odoo
- NetSuite
- SAP
- Custom SQL databases

See [docs/CONNECTORS.md](docs/CONNECTORS.md) for connector documentation.

### How does Sputnik learn and improve?

Sputnik uses on-policy distillation: it learns from its own rollouts (trajectories of tokens and tool calls) by comparing them to a teacher model's expectations. This provides dense, per-token learning signals that improve reliability over time.

See [docs/TECHNICAL.md](docs/TECHNICAL.md) for deep technical details.

### Is Sputnik safe for production use?

Sputnik is currently in **alpha** status. While it includes safety features (read-only queries, validation), it should be tested thoroughly in non-production environments before production deployment.

### Can I contribute?

Yes! See [Contributing](#contributing) below.

### What's the license?

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`ruff check .`, `mypy src/`, `pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run linting
ruff check .

# Run type checking
mypy src/

# Run tests
pytest

# Format code
ruff format .
```

## Documentation

- [Technical Details](docs/TECHNICAL.md) - Deep dive into on-policy distillation
- [Connectors](docs/CONNECTORS.md) - ERP connector architecture
- [Safety](docs/SAFETY.md) - Security and safety features

## License

MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

Built with attention to reliability, safety, and continuous improvement. Designed for enterprise use cases where accuracy and trust are paramount.

---

**Sputnik**: Reliable AI reasoning on top of ERP systems.
