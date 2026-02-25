from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from models import RoleEnum, AccountTypeEnum, AccountStatusEnum, TransactionTypeEnum

# --- CUSTOMER SCHEMAS ---
class CustomerCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: Optional[RoleEnum] = RoleEnum.customer

class CustomerResponse(BaseModel):
    id: str
    username: str
    role: RoleEnum
    created_at: datetime

    class Config:
        from_attributes = True

# --- ACCOUNT SCHEMAS ---
class AccountCreate(BaseModel):
    customer_id: str
    account_type: Optional[AccountTypeEnum] = AccountTypeEnum.checking

class AccountResponse(BaseModel):
    id: str
    customer_id: str
    account_type: AccountTypeEnum
    balance: Decimal
    status: AccountStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True

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
