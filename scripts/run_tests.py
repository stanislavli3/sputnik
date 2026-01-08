"""Quick test runner for Sputnik system."""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sputnik.agent.planner import Planner
from sputnik.agent.sql_generator import SQLGenerator
from sputnik.env.duckdb_env import DuckDBEnv


# Quick test queries
QUICK_TESTS = [
    "How many customers are there?",
    "What is the total amount of all orders?",
    "Show me all completed orders",
    "List customers with their order counts",
    "What is the average order amount?",
    "Find unpaid invoices",
    "Show orders from 2024",
    "Which customer has the most orders?",
    "Calculate total revenue",
    "give info",
]

# Comprehensive test categories
TEST_CATEGORIES = {
    "Basic Information": [
        "give info",
        "How many customers are there?",
        "What is the total number of orders?",
        "Count all invoices",
    ],
    "Simple Retrieval": [
        "List all customers",
        "Show me all orders",
        "Display all invoices",
    ],
    "Aggregations": [
        "What is the total amount of all orders?",
        "What is the average order amount?",
        "What is the maximum order amount?",
    ],
    "Filtered Queries": [
        "Show me all completed orders",
        "List all unpaid invoices",
        "Find customers from USA",
    ],
    "Joins": [
        "Show customer names with their orders",
        "List orders with customer information",
    ],
    "Complex Analysis": [
        "What is the total revenue from completed orders?",
        "Calculate average order value per customer",
        "Show total outstanding invoice amounts",
    ],
}


def test_query(question: str, env: DuckDBEnv, planner: Planner, sql_generator: SQLGenerator) -> dict:
    """Test a single query."""
    try:
        # Plan
        steps = planner.plan(question)
        
        # Generate SQL
        sql_queries = sql_generator.generate(question)
        
        # Execute queries
        results = []
        for sql_query in sql_queries:
            try:
                query_results = env.execute_query(sql_query)
                results.append({
                    "query": sql_query.query,
                    "results": query_results[:3],  # First 3 rows
                    "row_count": len(query_results),
                })
            except Exception as e:
                results.append({
                    "query": sql_query.query,
                    "error": str(e),
                })
        
        return {
            "question": question,
            "status": "success",
            "steps": steps,
            "sql_count": len(sql_queries),
            "results": results,
        }
    except Exception as e:
        return {
            "question": question,
            "status": "error",
            "error": str(e),
        }


def run_quick_tests():
    """Run quick test suite."""
    print("=" * 60)
    print("Sputnik Quick Test Suite")
    print("=" * 60)
    print()
    
    # Initialize environment
    db_path = "demo_erp.duckdb"
    try:
        env = DuckDBEnv(db_path)
        schema = env.get_schema()
        print(f"✓ Connected to database: {db_path}")
        print(f"✓ Found {len(schema.tables)} tables")
        print()
    except Exception as e:
        error_msg = str(e)
        if "lock" in error_msg.lower() or "conflicting" in error_msg.lower():
            print(f"✗ Database is locked by another process (likely the backend server)")
            print()
            print("Solutions:")
            print("  1. Stop the backend server, then run tests again")
            print("  2. Or test via the API instead (backend must be running)")
            print("     Use: python scripts/test_api.py")
            print()
            print("To stop backend: Press Ctrl+C in the terminal running the server")
            return
        else:
            print(f"✗ Error connecting to database: {e}")
            print("Please run: python scripts/setup_demo_db.py")
            return
    
    # Initialize components
    planner = Planner()
    sql_generator = SQLGenerator(schema)
    
    # Run tests
    passed = 0
    failed = 0
    
    for i, question in enumerate(QUICK_TESTS, 1):
        print(f"Test {i}/{len(QUICK_TESTS)}: {question}")
        result = test_query(question, env, planner, sql_generator)
        
        if result["status"] == "success":
            print(f"  ✓ Success - Generated {result['sql_count']} SQL query(ies)")
            if result["results"]:
                first_result = result["results"][0]
                if "error" in first_result:
                    print(f"  ⚠ Warning - Query error: {first_result['error']}")
                    failed += 1
                else:
                    print(f"  ✓ Returned {first_result.get('row_count', 0)} rows")
                    passed += 1
            else:
                print(f"  ⚠ No results returned")
                failed += 1
        else:
            print(f"  ✗ Failed - {result.get('error', 'Unknown error')}")
            failed += 1
        print()
    
    # Summary
    print("=" * 60)
    print(f"Test Summary: {passed} passed, {failed} failed out of {len(QUICK_TESTS)} tests")
    print("=" * 60)
    
    env.close()


def run_category_tests(category: str = None):
    """Run tests for a specific category or all categories."""
    print("=" * 60)
    print("Sputnik Comprehensive Test Suite")
    print("=" * 60)
    print()
    
    # Initialize environment
    db_path = "demo_erp.duckdb"
    try:
        env = DuckDBEnv(db_path)
        schema = env.get_schema()
        print(f"✓ Connected to database: {db_path}")
        print(f"✓ Found {len(schema.tables)} tables")
        print()
    except Exception as e:
        error_msg = str(e)
        if "lock" in error_msg.lower() or "conflicting" in error_msg.lower():
            print(f"✗ Database is locked by another process (likely the backend server)")
            print()
            print("Solutions:")
            print("  1. Stop the backend server, then run tests again")
            print("  2. Or test via the API instead (backend must be running)")
            print("     Use: python scripts/test_api.py")
            print()
            print("To stop backend: Press Ctrl+C in the terminal running the server")
            return
        else:
            print(f"✗ Error connecting to database: {e}")
            print("Please run: python scripts/setup_demo_db.py")
            return
    
    # Initialize components
    planner = Planner()
    sql_generator = SQLGenerator(schema)
    
    # Select categories to test
    categories_to_test = {category: TEST_CATEGORIES[category]} if category else TEST_CATEGORIES
    
    total_passed = 0
    total_failed = 0
    
    for cat_name, questions in categories_to_test.items():
        print(f"\n{'=' * 60}")
        print(f"Category: {cat_name}")
        print(f"{'=' * 60}")
        
        for question in questions:
            print(f"\nTesting: {question}")
            result = test_query(question, env, planner, sql_generator)
            
            if result["status"] == "success":
                print(f"  ✓ Success")
                print(f"    - Planning steps: {len(result.get('steps', []))}")
                print(f"    - SQL queries: {result['sql_count']}")
                if result["results"]:
                    first_result = result["results"][0]
                    if "error" in first_result:
                        print(f"    ⚠ Query error: {first_result['error']}")
                        total_failed += 1
                    else:
                        print(f"    ✓ Rows returned: {first_result.get('row_count', 0)}")
                        total_passed += 1
                else:
                    print(f"    ⚠ No results")
                    total_failed += 1
            else:
                print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
                total_failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Test Summary: {total_passed} passed, {total_failed} failed")
    print("=" * 60)
    
    env.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Sputnik system tests")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test suite (10 queries)",
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=list(TEST_CATEGORIES.keys()),
        help="Run tests for a specific category",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all comprehensive tests",
    )
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_tests()
    elif args.category:
        run_category_tests(args.category)
    elif args.all:
        run_category_tests()
    else:
        # Default to quick tests
        run_quick_tests()
