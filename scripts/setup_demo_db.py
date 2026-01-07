"""Setup script for creating a demo ERP database."""

import sys
from pathlib import Path

import duckdb

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def create_demo_database(db_path: str = "demo_erp.duckdb") -> None:
    """
    Create a demo ERP database with sample tables.

    Args:
        db_path: Path to the database file
    """
    conn = duckdb.connect(db_path)

    # Create customers table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name VARCHAR,
            email VARCHAR,
            created_at TIMESTAMP,
            country VARCHAR
        )
        """
    )

    # Create orders table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date DATE,
            total_amount DECIMAL(10, 2),
            status VARCHAR,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
        """
    )

    # Create invoices table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            invoice_date DATE,
            amount DECIMAL(10, 2),
            paid BOOLEAN,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
        """
    )

    # Create inventory_movements table
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS inventory_movements (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            movement_type VARCHAR,
            quantity INTEGER,
            movement_date DATE,
            warehouse_id INTEGER
        )
        """
    )

    # Insert sample data
    conn.execute(
        """
        INSERT INTO customers (id, name, email, created_at, country) VALUES
        (1, 'Acme Corp', 'contact@acme.com', '2024-01-15', 'USA'),
        (2, 'Beta Inc', 'info@beta.com', '2024-02-20', 'UK'),
        (3, 'Gamma LLC', 'hello@gamma.com', '2024-03-10', 'USA')
        """
    )

    conn.execute(
        """
        INSERT INTO orders (id, customer_id, order_date, total_amount, status) VALUES
        (1, 1, '2024-04-01', 1500.00, 'completed'),
        (2, 1, '2024-04-15', 2300.50, 'completed'),
        (3, 2, '2024-05-01', 850.00, 'pending'),
        (4, 3, '2024-05-10', 4200.75, 'completed')
        """
    )

    conn.execute(
        """
        INSERT INTO invoices (id, order_id, invoice_date, amount, paid) VALUES
        (1, 1, '2024-04-02', 1500.00, true),
        (2, 2, '2024-04-16', 2300.50, true),
        (3, 3, '2024-05-02', 850.00, false),
        (4, 4, '2024-05-11', 4200.75, true)
        """
    )

    conn.execute(
        """
        INSERT INTO inventory_movements (id, product_id, movement_type, quantity, movement_date, warehouse_id) VALUES
        (1, 101, 'in', 100, '2024-01-10', 1),
        (2, 101, 'out', 25, '2024-02-15', 1),
        (3, 102, 'in', 50, '2024-03-01', 1),
        (4, 101, 'out', 30, '2024-04-01', 1),
        (5, 103, 'in', 200, '2024-04-20', 2)
        """
    )

    conn.close()
    print(f"Demo database created at: {db_path}")
    print("Tables: customers, orders, invoices, inventory_movements")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup demo ERP database")
    parser.add_argument(
        "--db-path",
        type=str,
        default="demo_erp.duckdb",
        help="Path to database file",
    )
    args = parser.parse_args()

    create_demo_database(args.db_path)

