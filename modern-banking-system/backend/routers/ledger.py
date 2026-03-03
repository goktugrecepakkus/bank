from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List
from database import get_db
import models
import schemas
from security import get_current_user, get_current_admin

router = APIRouter(prefix="/ledger", tags=["Ledger & Transfers"])

@router.post("/transfer", response_model=schemas.LedgerResponse)
def create_transfer(transfer: schemas.TransferRequest, db: Session = Depends(get_db)):
    # 1. Hesapların var olup olmadığını kontrol et
    from_account = db.query(models.Account).filter(models.Account.id == transfer.from_account_id).first()
    to_account = db.query(models.Account).filter(models.Account.id == transfer.to_account_id).first()

    if not from_account or not to_account:
        raise HTTPException(status_code=404, detail="One or both accounts not found")

    if from_account.status != models.AccountStatusEnum.active or to_account.status != models.AccountStatusEnum.active:
        raise HTTPException(status_code=400, detail="One or both accounts are not ACTIVE")

    if from_account.id == to_account.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    # Global AML & MASAK Compliance Limit (e.g., max 100,000 TRY)
    if transfer.amount > 100000:
        raise HTTPException(
            status_code=403, 
            detail="Transaction exceeds MASAK/AML limits of 100,000 TRY. Please contact your branch for large transactions."
        )

    # 2. Bakiye kontrolü (Yetersiz Bakiye mi?)
    if from_account.balance < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # 4. HESAP BAKIYELERINI GUNCELLE (Önce bakiye güncellenir)
    from_account.balance -= transfer.amount
    to_account.balance += transfer.amount

    # 3. LEDGER KAYDI OLUSTUR (Single Source of Truth)
    new_ledger_entry = models.Ledger(
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=transfer.amount,
        transaction_type=models.TransactionTypeEnum.transfer
    )
    db.add(new_ledger_entry)

    # Tüm işlemleri veritabanına tek bir Transaction (Commit) olarak yaz!
    # Eğer bu satırlardan birinde hata çıkarsa, hiçbir şey veritabanına yazılmaz (Güvenlik)
    db.commit()
    db.refresh(new_ledger_entry)

    return new_ledger_entry

@router.post("/deposit", response_model=schemas.LedgerResponse)
def deposit_money(account_id: str, amount: Decimal, db: Session = Depends(get_db)):
    """Sisteme dış finansal kanallardan (simüle edilmiş) para girişi"""
    if amount <= 0:
         raise HTTPException(status_code=400, detail="Amount must be greater than zero")
            
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    new_ledger_entry = models.Ledger(
        from_account_id=None, # Para dışarıdan geliyor
        to_account_id=account.id,
        amount=amount,
        transaction_type=models.TransactionTypeEnum.deposit
    )
    db.add(new_ledger_entry)
    
    account.balance += amount
    db.commit()
    db.refresh(new_ledger_entry)
    
    return new_ledger_entry

@router.get("/history/{account_id}", response_model=List[schemas.LedgerResponse])
def get_account_history(account_id: str, db: Session = Depends(get_db)):
    """Belirli bir hesaba ait tüm Ledger (Para giriş/çıkış) hareketlerini listeler."""
    history = db.query(models.Ledger).filter(
        (models.Ledger.from_account_id == account_id) | 
        (models.Ledger.to_account_id == account_id)
    ).order_by(models.Ledger.created_at.desc()).all()
    return history

@router.get("/audit/all", response_model=List[schemas.LedgerResponse])
def get_audit_log(admin_user: models.Customer = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Sadece Adminlerin erişebileceği, tüm finansal hareketleri kronolojik listeleyen API"""
    audit = db.query(models.Ledger).order_by(models.Ledger.created_at.desc()).limit(100).all()
    return audit

@router.get("/audit/summary", response_model=schemas.AuditSummaryResponse)
def get_audit_summary(admin_user: models.Customer = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Sadece Adminlerin erişebileceği, bankanın genel özet metriklerini döndüren API"""
    total_users = db.query(models.Customer).count()
    total_accounts = db.query(models.Account).count()
    total_liquidity = db.query(func.sum(models.Account.balance)).scalar() or 0
    total_transactions = db.query(models.Ledger).count()
    
    return {
        "total_users": total_users,
        "total_accounts": total_accounts,
        "total_liquidity": total_liquidity,
        "total_transactions": total_transactions
    }
