"""Query optimization utilities."""

import re
from typing import List, Optional, Dict, Any


def analyze_query_performance(sql: str) -> Dict[str, Any]:
    """
    Analyze SQL query for potential performance issues.
    
    Args:
        sql: SQL query string
        
    Returns:
        Dictionary with analysis results
    """
    sql_upper = sql.upper()
    
    issues = []
    suggestions = []
    complexity_score = 0
    
    # Check for missing WHERE clause on large tables
    if "SELECT" in sql_upper and "FROM" in sql_upper:
        if "WHERE" not in sql_upper:
            issues.append("missing_where_clause")
            suggestions.append("Consider adding a WHERE clause to filter results")
            complexity_score += 1
    
    # Check for SELECT *
    if "SELECT *" in sql_upper:
        issues.append("select_all")
        suggestions.append("Consider selecting specific columns instead of *")
        complexity_score += 1
    
    # Check for multiple JOINs
    join_count = sql_upper.count("JOIN")
    if join_count > 3:
        issues.append("many_joins")
        suggestions.append(f"Query has {join_count} JOINs - consider if all are necessary")
        complexity_score += join_count - 2
    
    # Check for subqueries
    subquery_count = sql_upper.count("SELECT") - 1
    if subquery_count > 0:
        issues.append("subqueries")
        suggestions.append(f"Query contains {subquery_count} subquery(ies) - consider using JOINs")
        complexity_score += subquery_count
    
    # Check for ORDER BY without LIMIT
    if "ORDER BY" in sql_upper and "LIMIT" not in sql_upper:
        issues.append("order_by_without_limit")
        suggestions.append("Consider adding LIMIT when using ORDER BY")
        complexity_score += 1
    
    # Check for LIKE with leading wildcard
    if re.search(r"LIKE\s+['\"]%", sql_upper):
        issues.append("leading_wildcard")
        suggestions.append("LIKE queries with leading % cannot use indexes efficiently")
        complexity_score += 2
    
    # Estimate complexity
    if complexity_score < 3:
        complexity = "low"
    elif complexity_score < 6:
        complexity = "medium"
    else:
        complexity = "high"
    
    return {
        "complexity": complexity,
        "complexity_score": complexity_score,
        "issues": issues,
        "suggestions": suggestions,
        "join_count": join_count,
        "subquery_count": subquery_count,
    }


def optimize_query_hints(sql: str) -> List[str]:
    """
    Generate optimization hints for a query.
    
    Args:
        sql: SQL query string
        
    Returns:
        List of optimization hints
    """
    analysis = analyze_query_performance(sql)
    return analysis["suggestions"]


def estimate_query_cost(sql: str, table_stats: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    Estimate query execution cost.
    
    Args:
        sql: SQL query string
        table_stats: Dictionary mapping table names to row counts
        
    Returns:
        Estimated cost information
    """
    sql_upper = sql.upper()
    
    # Extract table names
    table_pattern = r"FROM\s+(\w+)"
    tables = re.findall(table_pattern, sql_upper, re.IGNORECASE)
    
    # Estimate row count
    estimated_rows = 1000  # Default estimate
    if table_stats and tables:
        # Use largest table as base estimate
        max_rows = max(
            (table_stats.get(table, 1000) for table in tables),
            default=1000
        )
        estimated_rows = max_rows
    
    # Adjust based on WHERE clause
    if "WHERE" in sql_upper:
        estimated_rows = int(estimated_rows * 0.1)  # Assume 10% filtered
    
    # Adjust based on JOINs
    join_count = sql_upper.count("JOIN")
    if join_count > 0:
        estimated_rows = int(estimated_rows * (join_count + 1))
    
    # Categorize cost
    if estimated_rows < 1000:
        cost_level = "low"
    elif estimated_rows < 10000:
        cost_level = "medium"
    else:
        cost_level = "high"
    
    return {
        "estimated_rows": estimated_rows,
        "cost_level": cost_level,
        "tables_involved": len(tables),
        "join_count": join_count,
    }
