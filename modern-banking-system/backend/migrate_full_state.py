from sqlalchemy import create_engine, text
import uuid

# Configuration
SUPABASE_URL = "postgresql://postgres.vlhcpntkzaonpnkgwjht:fN1TYqng0bZNm5rI@aws-1-ap-northeast-2.pooler.supabase.com:6543/postgres?sslmode=require"
LOCAL_URL = "postgresql://bankadmin:securepassword@db:5432/banking_db"
USERNAME = "Zaguney"

def migrate():
    local_engine = create_engine(LOCAL_URL)
    supabase_engine = create_engine(SUPABASE_URL)
    
    with local_engine.connect() as local_conn:
        # Get local user ID
        user_res = local_conn.execute(text("SELECT id FROM customers WHERE username = :u"), {"u": USERNAME}).fetchone()
        if not user_res:
            print("Local user not found.")
            return
        local_user_id = user_res[0]
        
        # Get accounts
        accounts = local_conn.execute(text("SELECT * FROM accounts WHERE customer_id = :uid"), {"uid": local_user_id}).fetchall()
        
        # Get cards
        cards = local_conn.execute(text("SELECT * FROM cards WHERE customer_id = :uid"), {"uid": local_user_id}).fetchall()

    with supabase_engine.connect() as sb_conn:
        # Get Supabase user ID for Zaguney
        sb_user_res = sb_conn.execute(text("SELECT id FROM customers WHERE username = :u"), {"u": USERNAME}).fetchone()
        if not sb_user_res:
            print("Supabase user not found. Ensure the user profile was created first.")
            return
        sb_user_id = sb_user_res[0]

        # Clean existing accounts/cards on Supabase for this user to avoid conflicts
        sb_conn.execute(text("DELETE FROM cards WHERE customer_id = :uid"), {"uid": sb_user_id})
        sb_conn.execute(text("DELETE FROM accounts WHERE customer_id = :uid"), {"uid": sb_user_id})
        sb_conn.commit()

        # Migrate Accounts
        print(f"Migrating {len(accounts)} accounts...")
        for acc in accounts:
            # Map local account data to Supabase (assuming same schema)
            # Row index depends on SELECT * order, safer to use keys if possible
            sb_conn.execute(text("""
                INSERT INTO accounts (id, customer_id, iban, account_type, currency, balance, status, created_at)
                VALUES (:id, :cid, :iban, :type, :curr, :bal, :stat, :cat)
            """), {
                "id": acc.id,
                "cid": sb_user_id,
                "iban": acc.iban,
                "type": acc.account_type,
                "curr": acc.currency,
                "bal": acc.balance,
                "stat": acc.status,
                "cat": acc.created_at
            })
        
        # Migrate Cards
        print(f"Migrating {len(cards)} cards...")
        for card in cards:
            sb_conn.execute(text("""
                INSERT INTO cards (id, customer_id, account_id, card_number, card_holder_name, expiry_date, cvv, card_type, status, credit_limit, current_debt, is_domestic_online, is_international_online, created_at)
                VALUES (:id, :cid, :aid, :num, :name, :exp, :cvv, :type, :stat, :lim, :debt, :dom, :int, :cat)
            """), {
                "id": card.id,
                "cid": sb_user_id,
                "aid": card.account_id,
                "num": card.card_number,
                "name": card.card_holder_name,
                "exp": card.expiry_date,
                "cvv": card.cvv,
                "type": card.card_type,
                "stat": card.status,
                "lim": card.credit_limit,
                "debt": card.current_debt,
                "dom": card.is_domestic_online,
                "int": card.is_international_online,
                "cat": card.created_at
            })
        
        sb_conn.commit()
        print("Migration complete.")

if __name__ == "__main__":
    migrate()
