from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from security import get_current_user
from rate_limiter import limiter

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
    
    # Not: Gerçek bir sistemde bu noktada karşı bankanın API'sine istek atılırdı.
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
