import sys
import os
from decimal import Decimal

# Add backend directory to sys.path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import SessionLocal
from models import Account
from routers.trading import get_live_price_in_try

def fix_cost_basis():
    db = SessionLocal()
    accounts = db.query(Account).filter(Account.currency != 'TRY').all()
    count = 0
    for acc in accounts:
        if float(acc.balance) > 0:
            current_price = float(get_live_price_in_try(acc.currency))
            # Calculate what the cost basis SHOULD be to equal 0% PnL right now
            ideal_cost_basis = float(acc.balance) * current_price
            
            # If cost basis is 0, or if the PnL is > 50% exactly (indicating migration corruption)
            if acc.cost_basis_try == 0 or (acc.cost_basis_try is None):
                print(f"Fixing {acc.currency} (Balance: {acc.balance}). Old Basis: {acc.cost_basis_try}. New Basis: {ideal_cost_basis}")
                acc.cost_basis_try = ideal_cost_basis
                count += 1
            elif ideal_cost_basis > 0 and acc.cost_basis_try > 0:
                current_avg = float(acc.cost_basis_try) / float(acc.balance)
                pnl = (current_price - current_avg) / current_avg
                if pnl > 0.5: # 50% corrupted profit
                    print(f"Normalizing high-profit {acc.currency} (Bal: {acc.balance}). Profit was {pnl*100}%. Resetting base to {ideal_cost_basis}.")
                    acc.cost_basis_try = ideal_cost_basis
                    count += 1
                    
    db.commit()
    db.close()
    print(f"Successfully fixed {count} accounts.")

if __name__ == '__main__':
    fix_cost_basis()
