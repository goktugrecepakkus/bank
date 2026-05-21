from sqlalchemy import create_engine, text

# Supabase URL
SUPABASE_URL = "postgresql://postgres.vlhcpntkzaonpnkgwjht:fN1TYqng0bZNm5rI@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require"
# Local URL
LOCAL_URL = "postgresql://bankadmin:securepassword@db:5432/banking_db"

def search_db(url, label):
    engine = create_engine(url)
    print(f"--- Searching {label} ---")
    with engine.connect() as conn:
        # Find users with more than 2 accounts or having specific currencies
        query = text("""
            SELECT c.username, COUNT(a.id) as account_count, string_agg(DISTINCT a.currency, ', ') as currencies, 
                   (SELECT COUNT(*) FROM cards WHERE customer_id = c.id) as card_count
            FROM customers c
            LEFT JOIN accounts a ON c.id = a.customer_id
            GROUP BY c.id, c.username
            HAVING COUNT(a.id) > 1 OR (SELECT COUNT(*) FROM cards WHERE customer_id = c.id) > 1
        """)
        results = conn.execute(query).fetchall()
        for row in results:
            print(f"User: {row[0]} | Accounts: {row[1]} | Currencies: {row[2]} | Cards: {row[3]}")

if __name__ == "__main__":
    # Search Supabase
    try:
        search_db(SUPABASE_URL, "Supabase")
    except Exception as e:
        print(f"Supabase error: {e}")
    
    # Search Local
    try:
        search_db(LOCAL_URL, "Local")
    except Exception as e:
        print(f"Local error: {e}")
