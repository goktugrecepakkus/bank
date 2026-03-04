from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from models import generate_iban
from typing import Optional

router = APIRouter(tags=["Accounts"])

@router.post("/accounts", response_model=schemas.AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    # Müşteri var mı diye kontrol et
    customer = db.query(models.Customer).filter(models.Customer.id == account.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Müşterinin bu para biriminde zaten hesabı var mı kontrolü
    existing_account = db.query(models.Account).filter(
        models.Account.customer_id == account.customer_id,
        models.Account.currency == account.currency
    ).first()

    if existing_account:
        raise HTTPException(status_code=400, detail=f"User already has a {account.currency} account.")

    # Benzersiz IBAN üret
    iban = generate_iban()
    while db.query(models.Account).filter(models.Account.iban == iban).first():
        iban = generate_iban()

    new_account = models.Account(
        customer_id=account.customer_id,
        account_type=account.account_type,
        currency=account.currency,
        iban=iban,
        balance=0.00 # Yeni açılan hesap sıfır bakiye ile başlar
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

@router.get("/accounts/customer/{customer_id}")
def get_customer_accounts(customer_id: str, currency: Optional[models.CurrencyEnum] = None, db: Session = Depends(get_db)):
    """Frontend (Dashboard) için müşteriye ait hesapları getiren yardımcı endpoint. Currency ile filtrelenebilir."""
    query = db.query(models.Account).filter(models.Account.customer_id == customer_id)
    if currency:
        query = query.filter(models.Account.currency == currency)
    accounts = query.all()
    return accounts

@router.get("/accounts/validate-iban/{iban}")
def validate_account_by_iban(iban: str, db: Session = Depends(get_db)):
    """IBAN ile hesap doğrulama - Transfer yaparken kullanılır"""
    account = db.query(models.Account).filter(models.Account.iban == iban).first()
    if not account:
        raise HTTPException(status_code=404, detail="IBAN not found")
        
    owner = db.query(models.Customer).filter(models.Customer.id == account.customer_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
        
    username = owner.username
    if len(username) > 2:
        masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
    else:
        masked_username = username[0] + "*"
        
    return {"account_id": account.id, "iban": account.iban, "masked_owner": masked_username}

@router.get("/accounts/validate/{account_id}")
def validate_account(account_id: str, db: Session = Depends(get_db)):
    """Girilen Hesap Numarasının (Account ID) kime ait olduğunu güvenli (maskeli) bir şekilde döndürür"""
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    owner = db.query(models.Customer).filter(models.Customer.id == account.customer_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")
        
    username = owner.username
    if len(username) > 2:
        masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
    else:
        masked_username = username[0] + "*"
        
    return {"account_id": account.id, "iban": account.iban, "masked_owner": masked_username}

@router.get("/accounts/{account_id}", response_model=schemas.AccountResponse)
def get_account_balance(account_id: str, db: Session = Depends(get_db)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account
