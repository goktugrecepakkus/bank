from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
import os
import asyncio
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
def send_to_external_bank(request: Request, transfer_req: schemas.ExternalTransferRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: models.Customer = Depends(get_current_user)):
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
    
    # Send WebSocket message to Hub using ISO 20022 PACS.008 XML
    import asyncio
    import uuid
    from iso20022 import generate_pacs008_xml
    
    message_id = str(uuid.uuid4())
    to_bank_bic = transfer_req.to_iban[:5] if len(transfer_req.to_iban) > 5 else "UNKNOWN"
    
    # Customer name from current_user
    debtor_name = f"{current_user.first_name} {current_user.last_name}" if hasattr(current_user, 'first_name') else "Customer"
    
    from routers.ws_client import OUR_BANK_ID
    
    xml_payload = generate_pacs008_xml(
        message_id=message_id,
        tx_id=new_ledger_entry.transaction_id,
        amount=float(transfer_req.amount),
        currency="TRY", # Şimdilik sadece TRY varsayılıyor
        from_iban=from_account.iban,
        to_iban=transfer_req.to_iban,
        from_bank_bic=OUR_BANK_ID,
        to_bank_bic=to_bank_bic,
        debtor_name=debtor_name
    )
    
    # Determine routing: P2P or Hub
    is_p2p = to_iban.startswith("FINB")
    
    # Send WebSocket message
    import websockets
    async def send_p2p_transfer():
        try:
            # FinBank spec: wss://<url>/ws/inter-bank/{SENDER_BANK_CODE}
            # For now using a placeholder for FinBank's URL (should be in a config/db later)
            FINBANK_WS_URL = os.getenv("FINBANK_WS_URL", "ws://localhost:9999/ws/inter-bank/RYKRD")
            
            async with websockets.connect(FINBANK_WS_URL) as ws:
                await ws.send(xml_payload)
                print(f"[P2P Out] Sent pacs.008 to FinBank. Waiting for ACK...")
                
                # Wait for pacs.002 ACK
                try:
                    ack_xml = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    from iso20022 import parse_pacs002_xml
                    ack_data = parse_pacs002_xml(ack_xml)
                    if ack_data["status"] == "ACCP":
                        print(f"[P2P Out] Transfer ACCEPTED by FinBank: {ack_data['original_tx_id']}")
                    else:
                        print(f"[P2P Out] Transfer REJECTED by FinBank: {ack_data['status']}")
                except asyncio.TimeoutError:
                    print("[P2P Out] Timeout waiting for ACK from FinBank.")
        except Exception as e:
            print(f"[P2P Out] Failed to send P2P transfer: {e}")

    if is_p2p:
        background_tasks.add_task(send_p2p_transfer)
    elif ws_client.connection:
        background_tasks.add_task(ws_client.send_xml_message, xml_payload)
    else:
        print("Warning: No P2P routing match and Hub is disconnected.")
    
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
