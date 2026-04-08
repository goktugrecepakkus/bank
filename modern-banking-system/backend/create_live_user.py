from sqlalchemy import create_engine, text
import uuid

# Supabase URL from .env
DB_URL = "postgresql://postgres.vlhcpntkzaonpnkgwjht:fN1TYqng0bZNm5rI@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require"

# Details for Zaguney
user_id = str(uuid.uuid4())
username = "Zaguney"
password_hash = "$2b$12$fAvaihXLLpkBCLX5QzR0pOPj/igutr3rTa2ROZOaKEk5i/vnLuhYC" # Zaguney123!
first_name = "Zeynel Abidin"
last_name = "Güney"
address = "Nowhere Land mah. Nowhere sk. No:0"
phone_number = "11111111111"
national_id = "9876543210"
mothers_maiden_name = "Marika"
role = "customer"

engine = create_engine(DB_URL)

with engine.connect() as conn:
    print(f"Adding user {username} to live database...")
    query = text("""
        INSERT INTO customers (id, username, password_hash, first_name, last_name, address, phone_number, national_id, mothers_maiden_name, role)
        VALUES (:id, :username, :password_hash, :first_name, :last_name, :address, :phone_number, :national_id, :mothers_maiden_name, :role)
    """)
    conn.execute(query, {
        "id": user_id,
        "username": username,
        "password_hash": password_hash,
        "first_name": first_name,
        "last_name": last_name,
        "address": address,
        "phone_number": phone_number,
        "national_id": national_id,
        "mothers_maiden_name": mothers_maiden_name,
        "role": role
    })
    conn.commit()
    print("SUCCESS: User created on Supabase.")
