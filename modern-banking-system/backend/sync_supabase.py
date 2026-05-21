from sqlalchemy import create_engine, text

# Supabase URL from .env
DB_URL = "postgresql://postgres.vlhcpntkzaonpnkgwjht:fN1TYqng0bZNm5rI@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require"

# Hash for Zaguney123!
new_hash = "$2b$12$fAvaihXLLpkBCLX5QzR0pOPj/igutr3rTa2ROZOaKEk5i/vnLuhYC"

engine = create_engine(DB_URL)

with engine.connect() as conn:
    print(f"Connecting to live database...")
    result = conn.execute(text("UPDATE customers SET password_hash = :hash WHERE username = 'Zaguney'"), {"hash": new_hash})
    conn.commit()
    print(f"Rows affected: {result.rowcount}")
    if result.rowcount > 0:
        print("SUCCESS: Live database updated.")
    else:
        print("FAILED: User 'Zaguney' not found on live database.")
