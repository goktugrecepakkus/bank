from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from models import RoleEnum, AccountTypeEnum, AccountStatusEnum, TransactionTypeEnum

# --- CUSTOMER SCHEMAS ---
class CustomerCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    address: str = Field(..., min_length=5, max_length=255)
    phone_number: str = Field(..., min_length=10, max_length=20)
    national_id: str = Field(..., min_length=9, max_length=11)
    mothers_maiden_name: str = Field(..., min_length=2)
    role: Optional[RoleEnum] = RoleEnum.customer

class CustomerUpdatePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class CustomerResponse(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str
    address: str
    phone_number: str
    national_id: str
    role: RoleEnum
    created_at: datetime

    class Config:
        from_attributes = True

# --- ACCOUNT SCHEMAS ---
class AccountCreate(BaseModel):
    customer_id: str
    account_type: Optional[AccountTypeEnum] = AccountTypeEnum.checking
    currency: Optional[str] = "TRY"

class AccountResponse(BaseModel):
    id: str
    customer_id: str
    account_type: AccountTypeEnum
    currency: str
    balance: Decimal
    status: AccountStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True

# --- TRADING SCHEMAS ---
class TradeRequest(BaseModel):
    from_currency: str
    to_currency: str
    amount: Decimal = Field(..., gt=0) # Alınmak/Satılmak istenen tutar

class MarketPriceResponse(BaseModel):
    currency: str
    price_in_try: Decimal
    last_updated: datetime

# --- LEDGER / TRANSFER SCHEMAS ---
class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: Decimal = Field(..., gt=0) # Tutar her zaman 0'dan büyük olmalı

class LedgerResponse(BaseModel):
    transaction_id: str
    from_account_id: Optional[str]
    to_account_id: Optional[str]
    amount: Decimal
    transaction_type: TransactionTypeEnum
    created_at: datetime

    class Config:
        from_attributes = True

class AuditSummaryResponse(BaseModel):
    total_users: int
    total_accounts: int
    total_liquidity: Decimal
    total_transactions: int
