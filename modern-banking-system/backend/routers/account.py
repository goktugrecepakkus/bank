from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/accounts", tags=["Accounts"])

@router.post("/", response_model=schemas.AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    # Müşteri var mı diye kontrol et
    customer = db.query(models.Customer).filter(models.Customer.id == account.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    new_account = models.Account(
        customer_id=account.customer_id,
        account_type=account.account_type,
        balance=0.00 # Yeni açılan hesap sıfır bakiye ile başlar
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

@router.get("/customer/{customer_id}")
def get_customer_accounts(customer_id: str, db: Session = Depends(get_db)):
    """Frontend (Dashboard) için müşteriye ait hesapları getiren yardımcı endpoint"""
    accounts = db.query(models.Account).filter(models.Account.customer_id == customer_id).all()
    return accounts

@router.get("/{account_id}", response_model=schemas.AccountResponse)
def get_account_balance(account_id: str, db: Session = Depends(get_db)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account
