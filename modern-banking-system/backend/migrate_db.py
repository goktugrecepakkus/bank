import os
from sqlalchemy import text
from database import engine

def run_migration():
    print("Running migration to add mothers_maiden_name column...")
    with engine.connect() as conn:
        try:
            # Check if column exists first (SQLite uses PRAGMA, PostgreSQL uses information_schema)
            # Since we just want to run an ALTER, we can try to catch the exception if it already exists
            conn.execute(text("ALTER TABLE customers ADD COLUMN mothers_maiden_name VARCHAR NOT NULL DEFAULT 'Unknown';"))
            conn.commit()
            print("Migration successful: Added mothers_maiden_name to customers table.")
        except Exception as e:
            print(f"Migration error (column might already exist): {e}")

if __name__ == "__main__":
    run_migration()
