"""
Migration: Account tablosuna IBAN kolonu ekle ve mevcut hesaplara IBAN ata.
Vercel'de PostgreSQL (Supabase) için çalışır.
"""
import os
import sys

# Backend klasörünü path'e ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from sqlalchemy import text
from database import engine
from models import generate_iban

def run_migration():
    print("Running migration: Adding IBAN column to accounts table...")
    with engine.connect() as conn:
        # 1. IBAN kolonu ekle
        try:
            conn.execute(text("ALTER TABLE accounts ADD COLUMN iban VARCHAR(26) UNIQUE;"))
            conn.commit()
            print("✓ Added iban column to accounts table.")
        except Exception as e:
            print(f"Column might already exist: {e}")
            conn.rollback()

        # 2. Mevcut hesaplara IBAN ata (NULL olanlar)
        try:
            rows = conn.execute(text("SELECT id FROM accounts WHERE iban IS NULL")).fetchall()
            if rows:
                for row in rows:
                    iban = generate_iban()
                    # Benzersiz IBAN kontrolü
                    while True:
                        existing = conn.execute(
                            text("SELECT id FROM accounts WHERE iban = :iban"),
                            {"iban": iban}
                        ).fetchone()
                        if not existing:
                            break
                        iban = generate_iban()
                    
                    conn.execute(
                        text("UPDATE accounts SET iban = :iban WHERE id = :id"),
                        {"iban": iban, "id": row[0]}
                    )
                conn.commit()
                print(f"✓ Assigned IBAN to {len(rows)} existing accounts.")
            else:
                print("✓ All accounts already have IBANs.")
        except Exception as e:
            print(f"Error assigning IBANs: {e}")
            conn.rollback()

if __name__ == "__main__":
    run_migration()
