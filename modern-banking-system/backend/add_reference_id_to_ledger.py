import os
from sqlalchemy import text
from database import engine

def run_migration():
    print("Running migration to add reference_id column to ledger...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE ledger ADD COLUMN reference_id VARCHAR;"))
            conn.commit()
            print("Migration successful: Added reference_id to ledger table.")
        except Exception as e:
            print(f"Migration error (column might already exist): {e}")

if __name__ == "__main__":
    run_migration()
