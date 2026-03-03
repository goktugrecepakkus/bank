import uuid
import enum
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Enum, func
from sqlalchemy.orm import relationship
from backend.database import Base

# --- ENUMS ---
class RoleEnum(str, enum.Enum):
    admin = "admin"
    customer = "customer"

class AccountTypeEnum(str, enum.Enum):
    checking = "CHECKING"
    savings = "SAVINGS"

class AccountStatusEnum(str, enum.Enum):
    active = "ACTIVE"
    blocked = "BLOCKED"

class TransactionTypeEnum(str, enum.Enum):
    deposit = "DEPOSIT"
    withdrawal = "WITHDRAWAL"
    transfer = "TRANSFER"

class CurrencyEnum(str, enum.Enum):
    TRY = "TRY"
    USD = "USD"
    EUR = "EUR"
    BTC = "BTC"
    ETH = "ETH"
    SOL = "SOL"
    XAU = "XAU" # Gold
    XAG = "XAG" # Silver

# --- MODELS ---
class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # KYC Fields added
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    national_id = Column(String, unique=True, nullable=False)

    mothers_maiden_name = Column(String, nullable=False, server_default="Unknown")
    role = Column(Enum(RoleEnum), default=RoleEnum.customer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship -> Hesapları görebilmek için
    accounts = relationship("Account", back_populates="owner")

class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    account_type = Column(Enum(AccountTypeEnum), default=AccountTypeEnum.checking, nullable=False)
    currency = Column(String, default=CurrencyEnum.TRY.value, nullable=False)
    
    # Paralarla çalışırken her zaman Numeric (Decimal) kullanılır, Float hatalara neden olabilir!
    balance = Column(Numeric(precision=15, scale=2), default=0.00, nullable=False)
    status = Column(Enum(AccountStatusEnum), default=AccountStatusEnum.active, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    owner = relationship("Customer", back_populates="accounts")

class Ledger(Base):
    __tablename__ = "ledger"

    transaction_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_account_id = Column(String, ForeignKey("accounts.id"), nullable=True) # Para nerden çıktı?
    to_account_id = Column(String, ForeignKey("accounts.id"), nullable=True)   # Para nereye girdi?
    
    amount = Column(Numeric(precision=15, scale=2), nullable=False)            # Transfer edilen tutar
    transaction_type = Column(Enum(TransactionTypeEnum), nullable=False)       # DEPOSIT, WITHDRAWAL, TRANSFER
    created_at = Column(DateTime(timezone=True), server_default=func.now())    # İşlem zamanı
