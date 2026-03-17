from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import List
from datetime import datetime, timedelta
from database import get_db
from pydantic import BaseModel
import uuid
import json
import models
import schemas
from security import get_current_user, get_current_admin
from rate_limiter import limiter, TRANSFER_LIMIT

router = APIRouter(prefix="/ledger", tags=["Ledger & Transfers"])

DAILY_TRANSFER_LIMIT = Decimal("100000.00")
SUSPICIOUS_TRANSFER_THRESHOLD = Decimal("50000.00")

@router.post("/transfer", response_model=schemas.LedgerResponse)
@limiter.limit(TRANSFER_LIMIT)
def create_transfer(request: Request, transfer: schemas.TransferRequest, db: Session = Depends(get_db), current_user: models.Customer = Depends(get_current_user)):
    # 1. Hesapların var olup olmadığını kontrol et
    from_account = db.query(models.Account).filter(models.Account.id == transfer.from_account_id).first()
    
    # Hedef hesap ID veya IBAN olabilir.
    to_account_str = str(transfer.to_account_id).replace(" ", "")
    if to_account_str.upper().startswith("TR"):
        # IBAN ile arama yap
        to_account = db.query(models.Account).filter(models.Account.iban == to_account_str).first()
    else:
        # Normal UUID ID ile arama yap
        to_account = db.query(models.Account).filter(models.Account.id == transfer.to_account_id).first()

    if not from_account or not to_account:
        raise HTTPException(status_code=404, detail="One or both accounts not found")
        
    if from_account.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only transfer from your own accounts")

    if from_account.status != models.AccountStatusEnum.active or to_account.status != models.AccountStatusEnum.active:
        raise HTTPException(status_code=400, detail="One or both accounts are not ACTIVE")

    if from_account.id == to_account.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to the same account")

    # 2. Bakiye kontrolü (Yetersiz Bakiye mi?)
    if from_account.balance < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # 3. AML KONTROLLERI (Daily Limit Check)
    today = datetime.utcnow().date()
    start_of_day = datetime(today.year, today.month, today.day)
    
    daily_transfers = db.query(func.sum(models.Ledger.amount)).filter(
        models.Ledger.from_account_id == from_account.id,
        models.Ledger.created_at >= start_of_day
    ).scalar() or Decimal("0.00")
    
    if daily_transfers + transfer.amount > DAILY_TRANSFER_LIMIT:
        raise HTTPException(status_code=400, detail=f"Daily transfer limit of {DAILY_TRANSFER_LIMIT} exceeded")

    # ŞÜPHELİ İŞLEM LOGLAMA
    if transfer.amount >= SUSPICIOUS_TRANSFER_THRESHOLD:
        audit_log = models.AuditLog(
            customer_id=current_user.id,
            action="SUSPICIOUS_TRANSFER",
            details=f"Large transfer of {transfer.amount} to {to_account.id}",
            ip_address=request.client.host if request.client else "Unknown"
        )
        db.add(audit_log)

    # 4. HESAP BAKIYELERINI GUNCELLE (Önce bakiye güncellenir)
    from_account.balance -= transfer.amount
    to_account.balance += transfer.amount

    # 3. LEDGER KAYDI OLUSTUR (Double Entry)
    ref_id = str(uuid.uuid4())
    
    # DEBIT (from account)
    debit_entry = models.Ledger(
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=transfer.amount,
        transaction_type=models.TransactionTypeEnum.transfer,
        direction="DEBIT",
        reference_id=ref_id
    )
    
    # CREDIT (to account)
    credit_entry = models.Ledger(
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=transfer.amount,
        transaction_type=models.TransactionTypeEnum.transfer,
        direction="CREDIT",
        reference_id=ref_id
    )
    
    db.add(debit_entry)
    db.add(credit_entry)

    # EVENT MESSAGING LOGIC (Outbox Pattern)
    # 1. TransferCreated event
    evt_payload = {"transfer_id": ref_id, "amount": float(transfer.amount), "from": from_account.id, "to": to_account.id}
    db.add(models.OutboxEvent(aggregate_type="Transfer", aggregate_id=ref_id, event_type="TransferCreated", payload=json.dumps(evt_payload)))
    
    # 2. AccountDebited event
    db.add(models.OutboxEvent(aggregate_type="Account", aggregate_id=from_account.id, event_type="AccountDebited", payload=json.dumps({"amount": float(transfer.amount)})))
    
    # 3. AccountCredited event
    db.add(models.OutboxEvent(aggregate_type="Account", aggregate_id=to_account.id, event_type="AccountCredited", payload=json.dumps({"amount": float(transfer.amount)})))

    # 4. TransferCompleted event
    db.add(models.OutboxEvent(aggregate_type="Transfer", aggregate_id=ref_id, event_type="TransferCompleted", payload=json.dumps(evt_payload)))

    # Tüm işlemleri veritabanına tek bir Transaction (Commit) olarak yaz!
    db.commit()
    db.refresh(debit_entry)

    return debit_entry

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
        transaction_type=models.TransactionTypeEnum.deposit,
        direction="CREDIT"
    )
    db.add(new_ledger_entry)
    
    account.balance += amount
    db.commit()
    db.refresh(new_ledger_entry)
    
    return new_ledger_entry

@router.post("/withdrawal", response_model=schemas.LedgerResponse)
def withdraw_money(request: schemas.WithdrawalRequest, db: Session = Depends(get_db)):
    """Sistemden dışarı para çıkışı simülasyonu"""
    if request.amount <= 0:
         raise HTTPException(status_code=400, detail="Amount must be greater than zero")
            
    account = db.query(models.Account).filter(models.Account.id == request.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    if account.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    new_ledger_entry = models.Ledger(
        from_account_id=account.id,
        to_account_id=None, # Para dışarı gidiyor
        amount=request.amount,
        transaction_type=models.TransactionTypeEnum.withdrawal,
        direction="DEBIT"
    )
    db.add(new_ledger_entry)
    
    account.balance -= request.amount
    db.commit()
    db.refresh(new_ledger_entry)
    
    return new_ledger_entry

@router.get("/history/{account_id}", response_model=List[schemas.LedgerResponse])
def get_account_history(account_id: str, db: Session = Depends(get_db)):
    """Belirli bir hesaba ait tüm Ledger (Para giriş/çıkış) hareketlerini listeler."""
    history = db.query(models.Ledger).filter(
        ((models.Ledger.from_account_id == account_id) & (models.Ledger.direction == "DEBIT")) | 
        ((models.Ledger.to_account_id == account_id) & (models.Ledger.direction == "CREDIT")) |
        ((models.Ledger.from_account_id == account_id) & (models.Ledger.direction == None)) | # Legacy entries
        ((models.Ledger.to_account_id == account_id) & (models.Ledger.direction == None))
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
