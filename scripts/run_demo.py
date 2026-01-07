"""Interactive demo script for Sputnik."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sputnik.agent.planner import Planner
from sputnik.agent.sql_generator import SQLGenerator
from sputnik.env.duckdb_env import DuckDBEnv
from sputnik.types import AgentResponse, SQLQuery


def main() -> None:
    """Run interactive demo."""
    print("=" * 60)
    print("Sputnik: AI Reliability Layer for ERP Analytics")
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
        print(f"✗ Error connecting to database: {e}")
        print("Please run: python scripts/setup_demo_db.py")
        return

    # Initialize components
    planner = Planner()
    sql_generator = SQLGenerator(schema)

    print("Ask business questions about your ERP data.")
    print("Type 'quit' or 'exit' to stop.")
    print()

    while True:
        try:
            query = input("Question: ").strip()
            if not query:
                continue
            if query.lower() in ("quit", "exit", "q"):
                break

            # Plan
            steps = planner.plan(query)
            print(f"\nPlanning steps: {', '.join(steps)}")

            # Generate SQL
            sql_queries = sql_generator.generate(query)
            if sql_queries:
                print(f"\nGenerated {len(sql_queries)} SQL query(ies):")
                for i, sql_query in enumerate(sql_queries, 1):
                    print(f"  {i}. {sql_query.query}")

                # Execute queries
                print("\nResults:")
                for sql_query in sql_queries:
                    try:
                        results = env.execute_query(sql_query)
                        if results:
                            # Print first few rows
                            for row in results[:5]:
                                print(f"  {row}")
                            if len(results) > 5:
                                print(f"  ... ({len(results) - 5} more rows)")
                        else:
                            print("  (no results)")
                    except Exception as e:
                        print(f"  Error: {e}")

                # Generate response
                response = AgentResponse(
                    answer=f"Based on the query results, here is the answer to: {query}",
                    sql_queries=sql_queries,
                    confidence=0.85,
                    reasoning="Generated from SQL query results",
                )

                print(f"\nAnswer: {response.answer}")
                print(f"Confidence: {response.confidence:.2f}")
            else:
                print("\nNo SQL queries generated for this question.")

            print()

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

    env.close()
    print("\nGoodbye!")


if __name__ == "__main__":
    main()

