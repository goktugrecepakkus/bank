import sqlite3

def check_db():
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    
    print("--- CUSTOMERS TABLE ---")
    cursor.execute("PRAGMA table_info(customers)")
    for row in cursor.fetchall():
        print(row)
        
    print("\n--- ACCOUNTS TABLE ---")
    cursor.execute("PRAGMA table_info(accounts)")
    for row in cursor.fetchall():
        print(row)
        
    conn.close()

if __name__ == '__main__':
    check_db()
