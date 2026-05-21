from sqlalchemy import create_engine, text

# Supabase URL
SUPABASE_URL = "postgresql://postgres.vlhcpntkzaonpnkgwjht:fN1TYqng0bZNm5rI@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require"

engine = create_engine(SUPABASE_URL)
with engine.connect() as conn:
    print("--- Searching Supabase for BTC/ETH/EUR ---")
    query = text("""
        SELECT c.username, a.currency, a.balance, c.first_name, c.last_name
        FROM accounts a
        JOIN customers c ON a.customer_id = c.id
        WHERE a.currency IN ('BTC', 'ETH', 'EUR', 'USD')
    """)
    results = conn.execute(query).fetchall()
    if results:
        for row in results:
            print(f"User: {row[0]} | Currency: {row[1]} | Balance: {row[2]} | Name: {row[3]} {row[4]}")
    else:
        print("No users found with these assets on Supabase.")

    print("\n--- Searching Supabase for Users with multiple cards ---")
    query_cards = text("""
        SELECT c.username, COUNT(card.id) as card_cnt
        FROM cards card
        JOIN customers c ON card.customer_id = c.id
        GROUP BY c.username
        HAVING COUNT(card.id) > 1
    """)
    res_cards = conn.execute(query_cards).fetchall()
    if res_cards:
        for row in res_cards:
            print(f"User: {row[0]} | Card Count: {row[1]}")
    else:
        print("No users found with multiple cards on Supabase.")
