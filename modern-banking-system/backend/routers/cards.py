from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import random
import string
from datetime import datetime
from dateutil.relativedelta import relativedelta

from database import get_db
import models
import schemas
from security import get_current_user
from card_encryption import encrypt_card_field, decrypt_card_field


def _decrypt_card_response(card: models.Card) -> dict:
    """Kart verisini API response için çözümle"""
    return {
        "id": card.id,
        "customer_id": card.customer_id,
        "account_id": card.account_id,
        "card_number": decrypt_card_field(card.card_number),
        "card_holder_name": card.card_holder_name,
        "expiry_date": card.expiry_date,
        "cvv": decrypt_card_field(card.cvv),
        "card_type": card.card_type,
        "status": card.status,
        "credit_limit": card.credit_limit,
        "current_debt": card.current_debt,
        "is_domestic_online": card.is_domestic_online,
        "is_international_online": card.is_international_online,
        "created_at": card.created_at,
    }

router = APIRouter(
    prefix="/cards",
    tags=["cards"]
)

def generate_card_number(prefix: str = "4") -> str:
    """Generates a random 16-digit card number (e.g. starting with 4 for Visa)"""
    # Simply random 15 digits after the prefix (No Luhn algorithm check needed for demo)
    rest = ''.join(random.choices(string.digits, k=15))
    return prefix + rest

def generate_cvv() -> str:
    return ''.join(random.choices(string.digits, k=3))

def generate_expiry_date(years_valid: int = 5) -> str:
    future_date = datetime.now() + relativedelta(years=years_valid)
    return future_date.strftime("%m/%y")

@router.post("/", response_model=schemas.CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(card: schemas.CardCreate, db: Session = Depends(get_db), current_user: models.Customer = Depends(get_current_user)):
    # Security check: User can only create cards for themselves (unless admin)
    if current_user.id != card.customer_id and current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized to create a card for this user")

    # Verify customer exists
    customer = db.query(models.Customer).filter(models.Customer.id == card.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # If Debit Card, verify the account_id exists and belongs to the user
    if card.card_type == models.CardTypeEnum.debit:
        if not card.account_id:
            raise HTTPException(status_code=400, detail="An account ID is mandatory for a Debit Card")
        
        account = db.query(models.Account).filter(models.Account.id == card.account_id, models.Account.customer_id == card.customer_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Linked account not found or does not belong to the user")

    # Generate Details
    prefix = "4" if card.card_type == models.CardTypeEnum.debit else "5" # 4 for Visa (Debit), 5 for Mastercard (Credit)
    new_card_number = generate_card_number(prefix)
    
    # Ensure unique
    while db.query(models.Card).filter(models.Card.card_number == new_card_number).first():
        new_card_number = generate_card_number(prefix)

    new_cvv = generate_cvv()
    new_expiry = generate_expiry_date()

    credit_limit = 0.00
    if card.card_type == models.CardTypeEnum.credit:
        credit_limit = 50000.00 # Default limit for demo
        card.account_id = None # Credit cards might not link directly to a checking account out-of-the-box

    # PCI-DSS: Kart numarası ve CVV şifrelenerek saklanır
    encrypted_card_number = encrypt_card_field(new_card_number)
    encrypted_cvv = encrypt_card_field(new_cvv)

    db_card = models.Card(
        customer_id=card.customer_id,
        account_id=card.account_id,
        card_number=encrypted_card_number,
        card_holder_name=f"{customer.first_name} {customer.last_name}".upper(),
        expiry_date=new_expiry,
        cvv=encrypted_cvv,
        card_type=card.card_type,
        status=models.CardStatusEnum.active,
        credit_limit=credit_limit,
        current_debt=0.00
    )

    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return _decrypt_card_response(db_card)


@router.get("/customer/{customer_id}", response_model=List[schemas.CardResponse])
def get_customer_cards(customer_id: str, db: Session = Depends(get_db), current_user: models.Customer = Depends(get_current_user)):
    # Security check
    if current_user.id != customer_id and current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized to view these cards")

    cards = db.query(models.Card).filter(models.Card.customer_id == customer_id).all()
    return [_decrypt_card_response(c) for c in cards]

@router.put("/{card_id}/settings", response_model=schemas.CardResponse)
def update_card_settings(card_id: str, settings: schemas.CardSettingsUpdate, db: Session = Depends(get_db), current_user: models.Customer = Depends(get_current_user)):
    card = db.query(models.Card).filter(models.Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # User only
    if current_user.id != card.customer_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    card.is_domestic_online = settings.is_domestic_online
    card.is_international_online = settings.is_international_online
    db.commit()
    db.refresh(card)
    return _decrypt_card_response(card)

@router.post("/{card_id}/limit-request", response_model=schemas.LimitRequestResponse)
def create_limit_request(card_id: str, req: schemas.LimitRequestCreate, db: Session = Depends(get_db), current_user: models.Customer = Depends(get_current_user)):
    card = db.query(models.Card).filter(models.Card.id == card_id).first()
    if not card or card.customer_id != current_user.id:
        raise HTTPException(status_code=404, detail="Card not found or not owned by user")
    
    if card.card_type != models.CardTypeEnum.credit:
        raise HTTPException(status_code=400, detail="Limit requests are only for Credit Cards")

    new_req = models.LimitRequest(
        card_id=card_id,
        customer_id=current_user.id,
        requested_limit=req.requested_limit,
        status=models.LimitRequestStatusEnum.pending
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req

@router.get("/limit-requests/pending", response_model=List[schemas.LimitRequestResponse])
def get_pending_limit_requests(db: Session = Depends(get_db), current_user: models.Customer = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin only")
    
    return db.query(models.LimitRequest).filter(models.LimitRequest.status == models.LimitRequestStatusEnum.pending).all()

@router.put("/limit-requests/{request_id}", response_model=schemas.LimitRequestResponse)
def review_limit_request(request_id: str, review: schemas.LimitRequestReview, db: Session = Depends(get_db), current_user: models.Customer = Depends(get_current_user)):
    if current_user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Admin only")

    req = db.query(models.LimitRequest).filter(models.LimitRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    req.status = review.status
    
    if review.status == models.LimitRequestStatusEnum.approved:
        card = db.query(models.Card).filter(models.Card.id == req.card_id).first()
        if card:
            card.credit_limit = req.requested_limit
            
    db.commit()
    db.refresh(req)
    return req
