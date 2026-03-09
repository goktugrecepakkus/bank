from sqlalchemy import create_engine, text

# Supabase URL from .env
DB_URL = "postgresql://postgres.vlhcpntkzaonpnkgwjht:fN1TYqng0bZNm5rI@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require"

engine = create_engine(DB_URL)

with engine.connect() as conn:
    print(f"Connecting to live database...")
    result = conn.execute(text("SELECT username, first_name, last_name FROM customers"))
    users = result.fetchall()
    print(f"Users found: {len(users)}")
    for user in users:
        print(f"User: {user[0]} ({user[1]} {user[2]})")
