from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres.vlhcpntkzaonpnkgwjht:fN1TYqng0bZNm5rI@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require"
engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("Searching Supabase for 'Zeynel'...")
    query = text("SELECT username, first_name, last_name FROM customers WHERE username ILIKE '%Zeynel%' OR first_name ILIKE '%Zeynel%'")
    result = conn.execute(query).fetchall()
    if result:
        for row in result:
            print(f"Found: {row[0]} ({row[1]} {row[2]})")
    else:
        print("No users found matching 'Zeynel'.")
