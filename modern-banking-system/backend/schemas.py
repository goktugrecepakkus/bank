from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from models import RoleEnum, CustomerStatusEnum, AccountTypeEnum, AccountStatusEnum, TransactionTypeEnum, CardTypeEnum, CardStatusEnum

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
    status: CustomerStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True

class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code_url: str

class TwoFactorVerify(BaseModel):
    user_id: str
    token: str

class TwoFactorLogin(BaseModel):
    temp_token: str
    otp_code: str

class ForgotPasswordCardRequest(BaseModel):
    username: str
    card_number: str
    expiry_date: str
    cvv: str
    new_password: str = Field(..., min_length=6)

# --- ACCOUNT SCHEMAS ---
class AccountCreate(BaseModel):
    customer_id: str
    account_type: Optional[AccountTypeEnum] = AccountTypeEnum.checking
    currency: Optional[str] = "TRY"

class AccountResponse(BaseModel):
    id: str
    customer_id: str
    iban: Optional[str] = None
    account_type: AccountTypeEnum
    currency: str
    balance: Decimal
    cost_basis_try: Decimal
    status: AccountStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True

# --- CARD SCHEMAS ---
class CardCreate(BaseModel):
    customer_id: str
    card_type: CardTypeEnum
    account_id: Optional[str] = None # Mandatory for Debit cards

class CardResponse(BaseModel):
    id: str
    customer_id: str
    account_id: Optional[str]
    card_number: str
    card_holder_name: str
    expiry_date: str
    cvv: str
    card_type: CardTypeEnum
    status: CardStatusEnum
    credit_limit: Decimal
    current_debt: Decimal
    is_domestic_online: str
    is_international_online: str
    created_at: datetime

    class Config:
        from_attributes = True

class CardSettingsUpdate(BaseModel):
    is_domestic_online: str
    is_international_online: str

class LimitRequestCreate(BaseModel):
    card_id: str
    requested_limit: Decimal

class LimitRequestResponse(BaseModel):
    id: str
    card_id: str
    customer_id: str
    requested_limit: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class LimitRequestReview(BaseModel):
    status: str # APPROVED or REJECTED

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

class ExternalTransferRequest(BaseModel):
    from_account_id: str
    to_iban: str
    amount: Decimal = Field(..., gt=0)

class WithdrawalRequest(BaseModel):
    account_id: str
    amount: Decimal = Field(..., gt=0)

class ExternalReceiveRequest(BaseModel):
    to_account_iban: str
    from_iban: str
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None

class LedgerResponse(BaseModel):
    transaction_id: str
    from_account_id: Optional[str]
    to_account_id: Optional[str]
    amount: Decimal
    transaction_type: TransactionTypeEnum
    direction: Optional[str] = None
    reference_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AuditSummaryResponse(BaseModel):
    total_users: int
    total_accounts: int
    total_liquidity: Decimal
    total_transactions: int
