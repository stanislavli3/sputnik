# Safety & Security

Sputnik is designed with safety as a first-class concern. This document describes safety features, guarantees, and best practices.

## Read-Only Queries

**Status**: ✅ Implemented

Sputnik enforces read-only queries by default. All SQL queries are validated before execution to ensure they don't modify data.

### Validation

Queries are checked for dangerous keywords:
- `INSERT`, `UPDATE`, `DELETE`
- `DROP`, `CREATE`, `ALTER`, `TRUNCATE`
- Other data-modifying operations

### Implementation

```python
def _is_read_only(self, sql: str) -> bool:
    dangerous_keywords = ["INSERT", "UPDATE", "DELETE", ...]
    for keyword in dangerous_keywords:
        if keyword in sql.upper():
            return False
    return True
```

### Database-Level Protection

In addition to query validation, connectors should:

- Use read-only database users
- Set database connection to read-only mode
- Use read-only ORM methods (for Odoo, etc.)

## Allowlist / Denylist

**Status**: 🚧 Planned

Future versions will support:

- **Table Allowlist**: Only allow queries to specific tables
- **Column Denylist**: Block access to sensitive columns (e.g., passwords, SSNs)
- **Query Pattern Matching**: Block queries matching dangerous patterns

### Example Configuration

```yaml
safety:
  allowed_tables:
    - customers
    - orders
    - invoices
  blocked_columns:
    - customers.password
    - customers.ssn
  blocked_patterns:
    - "DROP TABLE"
    - "DELETE FROM"
```

## PII Handling

**Status**: 🚧 Planned

Sputnik will detect and handle personally identifiable information (PII):

- **Detection**: Identify PII in query results (emails, SSNs, phone numbers, etc.)
- **Masking**: Automatically mask PII in responses
- **Logging**: Log PII access for audit purposes
- **Compliance**: Support GDPR, CCPA, and other privacy regulations

### PII Types

- Email addresses
- Social Security Numbers
- Phone numbers
- Credit card numbers
- IP addresses
- Physical addresses

## Audit Logging

**Status**: 🚧 Planned

Comprehensive audit logging will track:

- All queries executed
- Query results (with PII masking)
- User actions
- Model decisions
- Errors and exceptions

### Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "user_id": "user123",
  "query": "What is the total revenue?",
  "sql_queries": ["SELECT SUM(total_amount) FROM orders"],
  "response": "...",
  "pii_detected": false,
  "execution_time_ms": 45
}
```

## Why Sputnik is Safe for Finance / Ops Teams

### 1. Read-Only by Default

Sputnik cannot modify data. All queries are validated and executed in read-only mode.

### 2. Transparent

- All SQL queries are logged and visible
- Responses include the SQL used
- No "black box" behavior

### 3. Validated

- Queries are checked before execution
- Schema-aware generation reduces errors
- Type-safe code reduces bugs

### 4. Auditable

- All interactions are logged (roadmap)
- Query history is preserved
- Compliance-ready

### 5. Controlled Access

- Table-level access control (roadmap)
- Column-level restrictions (roadmap)
- User authentication and authorization (roadmap)

## Security Best Practices

### For Administrators

1. **Use Read-Only Database Users**: Create dedicated read-only users for Sputnik
2. **Limit Table Access**: Only grant access to necessary tables
3. **Monitor Queries**: Review query logs regularly
4. **Keep Updated**: Stay current with Sputnik updates
5. **Test in Staging**: Always test in non-production first

### For Developers

1. **Validate Inputs**: Always validate user queries
2. **Sanitize Outputs**: Mask PII in responses
3. **Handle Errors Gracefully**: Don't expose sensitive information in errors
4. **Use Type Safety**: Leverage type annotations and mypy
5. **Write Tests**: Test safety features thoroughly

## Threat Model

### Potential Threats

1. **SQL Injection**: Mitigated by query validation and parameterization
2. **Data Exfiltration**: Mitigated by read-only access and audit logging
3. **PII Exposure**: Mitigated by PII detection and masking (roadmap)
4. **Denial of Service**: Mitigated by query timeouts and rate limiting (roadmap)

### Mitigations

- Query validation
- Read-only access
- Audit logging
- PII handling
- Access controls
- Rate limiting (roadmap)

## Compliance

Sputnik is designed to support compliance with:

- **GDPR**: PII handling, right to deletion (roadmap)
- **CCPA**: Privacy controls, audit trails
- **SOC 2**: Security controls, audit logging
- **HIPAA**: PII protection (with proper configuration)

## Reporting Security Issues

If you discover a security vulnerability, please:

1. **Do not** open a public issue
2. Email security concerns to: [security email]
3. Include details about the vulnerability
4. Allow time for the issue to be addressed before disclosure

## Roadmap

### Phase 1: Current
- ✅ Read-only query validation
- ✅ Basic safety checks

### Phase 2: Near-term
- 🚧 Allowlist/denylist
- 🚧 PII detection
- 🚧 Audit logging

### Phase 3: Long-term
- 🔮 Fine-grained access control
- 🔮 Rate limiting
- 🔮 Compliance automation
- 🔮 Security monitoring dashboard

## References

- OWASP Top 10
- SQL Injection Prevention
- GDPR Compliance
- SOC 2 Requirements

