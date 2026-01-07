# Connector Architecture

Sputnik uses a connector abstraction to support multiple ERP systems. This document describes the connector interface and implemented connectors.

## Connector Abstraction

All ERP connectors must provide:

1. **Query Execution**: Execute read-only SQL queries
2. **Schema Introspection**: Extract table and relationship information
3. **Safety Guarantees**: Ensure queries are read-only

### Interface

```python
class ERPConnector:
    def execute_query(self, query: SQLQuery) -> List[Dict[str, Any]]:
        """Execute a read-only SQL query."""
        pass
    
    def get_schema(self) -> ERPSchema:
        """Get the ERP schema."""
        pass
```

## DuckDB Connector

**Status**: ✅ Implemented

The DuckDB connector is used for demos and testing. It provides a lightweight, in-memory SQL database that simulates ERP systems.

### Features

- Full SQL support (read-only)
- Schema introspection
- In-memory or file-based storage
- Fast query execution

### Usage

```python
from sputnik.env.duckdb_env import DuckDBEnv

env = DuckDBEnv("demo_erp.duckdb")
schema = env.get_schema()
results = env.execute_query(sql_query)
```

### Demo Schema

The demo database includes:

- `customers`: Customer information
- `orders`: Order records
- `invoices`: Invoice records
- `inventory_movements`: Inventory tracking

See `scripts/setup_demo_db.py` for schema details.

## Odoo Connector

**Status**: 🚧 Planned

Odoo is a popular open-source ERP system. The connector will:

- Connect to Odoo via ORM or REST API
- Map Odoo models to SQL-like queries
- Support read-only access
- Introspect Odoo model schemas

### Implementation Plan

1. **ORM Access**: Use Odoo's Python ORM for read-only queries
2. **Schema Mapping**: Map Odoo models to ERPSchema format
3. **Query Translation**: Convert SQL-like queries to Odoo ORM calls
4. **Safety**: Enforce read-only access at the ORM level

## NetSuite Connector

**Status**: 🚧 Planned

NetSuite is a cloud-based ERP system. The connector will:

- Use NetSuite REST API or SuiteScript
- Support SuiteQL (NetSuite's SQL-like query language)
- Handle authentication and session management
- Map NetSuite records to ERPSchema

## SAP Connector

**Status**: 🚧 Planned

SAP is an enterprise ERP system. The connector will:

- Use SAP HANA SQL interface
- Support ABAP CDS views
- Handle SAP authentication
- Map SAP tables to ERPSchema

## Custom SQL Database Connector

**Status**: 🚧 Planned

A generic connector for any SQL database (PostgreSQL, MySQL, etc.):

- Standard SQL interface
- Database-specific optimizations
- Connection pooling
- Schema introspection via INFORMATION_SCHEMA

## Read-Only Guarantees

All connectors must enforce read-only access:

1. **Query Validation**: Check queries for dangerous keywords (INSERT, UPDATE, DELETE, etc.)
2. **Database-Level**: Use read-only database users/connections where possible
3. **ORM-Level**: Use read-only ORM methods (e.g., `search_read` in Odoo)
4. **API-Level**: Use read-only API endpoints

## Adding a New Connector

To add a new connector:

1. Create a new class inheriting from the connector interface
2. Implement `execute_query()` and `get_schema()`
3. Add read-only validation
4. Write tests
5. Update this documentation

Example:

```python
from sputnik.types import ERPSchema, SQLQuery

class MyERPConnector:
    def __init__(self, connection_string: str):
        # Initialize connection
        pass
    
    def execute_query(self, query: SQLQuery) -> List[Dict[str, Any]]:
        if not query.is_read_only:
            raise ValueError("Only read-only queries allowed")
        # Execute query
        pass
    
    def get_schema(self) -> ERPSchema:
        # Introspect schema
        pass
```

## Security Considerations

- **Authentication**: Each connector handles its own authentication
- **Authorization**: Connectors should use least-privilege access
- **Network**: Use encrypted connections (TLS/SSL)
- **Audit**: Log all queries (future feature)

## Performance

Connectors should:

- Use connection pooling where applicable
- Cache schema information
- Optimize query execution
- Handle timeouts gracefully

## Testing

Each connector should have:

- Unit tests for query execution
- Schema introspection tests
- Read-only validation tests
- Integration tests with sample data

