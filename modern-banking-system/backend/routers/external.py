from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from security import get_current_user
from rate_limiter import limiter
from routers.ws_client import ws_client
import uuid

router = APIRouter(prefix="/external", tags=["External Transfers"])

@router.post("/send", response_model=schemas.LedgerResponse)
@limiter.limit("5/minute")
def send_to_external_bank(request: Request, transfer_req: schemas.ExternalTransferRequest, db: Session = Depends(get_db), current_user: models.Customer = Depends(get_current_user)):
    """
    Rykard Bank'tan başka bir bankaya para gönderme.
    Kullanıcının bakiyesi düşer, Ledger'a EXTERNAL_TRANSFER (veya TRANSFER) olarak yansır.
    """
    from_account = db.query(models.Account).filter(models.Account.id == transfer_req.from_account_id, models.Account.customer_id == current_user.id).first()
    
    if not from_account:
        raise HTTPException(status_code=404, detail="Account not found or not owned by user")
        
    if from_account.status != models.AccountStatusEnum.active:
        raise HTTPException(status_code=400, detail="Account is not ACTIVE")
        
    # --- Regulatory Validations ---
    # 1. IBAN Check
    to_iban = transfer_req.to_iban.upper().replace(" ", "")
    if not to_iban.startswith("TR") or len(to_iban) != 26 or not to_iban[2:].isdigit():
        raise HTTPException(status_code=400, detail="Invalid Target IBAN format. Must start with TR and contain 24 digits.")
    
    # 2. Transaction Limits (AML / Security)
    MAX_SINGLE_TRANSACTION = 100000.00
    if float(transfer_req.amount) > MAX_SINGLE_TRANSACTION:
        # Audit log the suspicious high amount transfer attempt
        suspicious_audit = models.AuditLog(
            customer_id=current_user.id,
            action="SUSPICIOUS_TRANSFER_ATTEMPT",
            details=f"Attempted to external transfer {transfer_req.amount} TRY to {to_iban}",
            ip_address=request.client.host
        )
        db.add(suspicious_audit)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Transfer amount exceeds single transaction limit of {MAX_SINGLE_TRANSACTION} TRY")

    # 3. Daily Limit Check (AML / Security)
    from datetime import datetime, timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    daily_transfers_sum = db.query(models.Ledger).filter(
        models.Ledger.from_account_id == from_account.id,
        models.Ledger.transaction_type == models.TransactionTypeEnum.transfer,
        models.Ledger.created_at >= yesterday
    ).with_entities(models.func.sum(models.Ledger.amount)).scalar() or 0
    
    MAX_DAILY_LIMIT = 500000.00
    if float(daily_transfers_sum) + float(transfer_req.amount) > MAX_DAILY_LIMIT:
        raise HTTPException(status_code=400, detail=f"Transfer exceeds daily rolling limit of {MAX_DAILY_LIMIT} TRY")
        
    if from_account.balance < transfer_req.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
        
    # Bakiyeyi düşür
    from_account.balance -= transfer_req.amount
    
    # Ledger kaydı oluştur (to_account_id None, çünkü para dışarı çıkıyor)
    new_ledger_entry = models.Ledger(
        from_account_id=from_account.id,
        to_account_id=None,
        amount=transfer_req.amount,
        transaction_type=models.TransactionTypeEnum.transfer
    )
    db.add(new_ledger_entry)
    db.commit()
    db.refresh(new_ledger_entry)
    
    # Send WebSocket message to Hub
    import asyncio
    ws_payload = {
        "type": "TRANSFER",
        "tx_id": new_ledger_entry.transaction_id,
        "from_bank": ws_client.OUR_BANK_ID,
        "to_bank": transfer_req.to_iban[:5] if len(transfer_req.to_iban) > 5 else "UNKNOWN", # Basit bir tahmin, hedef banka bilgisi eklenebilir
        "to_account": transfer_req.to_iban,
        "amount": float(transfer_req.amount),
        "currency": "TRY" # Şimdilik sadece TRY varsayılıyor
    }
    
    # Use create_task since we are inside a sync route function (or could make route async)
    if ws_client.connection:
        asyncio.create_task(ws_client.send_message(ws_payload))
    else:
        print("Warning: WS Client is not connected, transfer simulated locally but message not sent.")
    
    return new_ledger_entry

@router.post("/receive", response_model=schemas.LedgerResponse)
@limiter.limit("50/minute") 
def receive_from_external_bank(request: Request, receive_req: schemas.ExternalReceiveRequest, db: Session = Depends(get_db)):
    """
    Başka bir bankadan Rykard Bank müşterisine para gelmesi (Webhook).
    Gerçekte bu endpoint API Key veya IP bazlı korunmalıdır.
    """
    to_account = db.query(models.Account).filter(models.Account.iban == receive_req.to_account_iban).first()
    
    if not to_account:
        raise HTTPException(status_code=404, detail="Target account IBAN not found")
        
    if to_account.status != models.AccountStatusEnum.active:
        raise HTTPException(status_code=400, detail="Target account is not ACTIVE")
        
    # Bakiyeyi artır
    to_account.balance += receive_req.amount
    
    # Ledger kaydı oluştur (from_account_id None, çünkü para dışarıdan geliyor)
    new_ledger_entry = models.Ledger(
        from_account_id=None,
        to_account_id=to_account.id,
        amount=receive_req.amount,
        transaction_type=models.TransactionTypeEnum.deposit
    )
    db.add(new_ledger_entry)
    db.commit()
    db.refresh(new_ledger_entry)
    
    return new_ledger_entry
