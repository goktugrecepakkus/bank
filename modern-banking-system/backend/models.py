import uuid
import enum
import random
from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime, Enum, func
from sqlalchemy.orm import relationship
from database import Base


def generate_iban():
    """Türk bankacılık standardına uygun rastgele IBAN üretir (TR + 24 rakam = 26 karakter)"""
    bank_code = "00061"  # RykardBank kodu
    account_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
    # IBAN kontrol rakamı hesaplama (ISO 13616)
    bban = bank_code + account_number
    # TR00 + BBAN -> sayısal forma çevir (T=29, R=27)
    numeric_str = bban + "292700"
    check_digits = 98 - (int(numeric_str) % 97)
    return f"TR{check_digits:02d}{bban}"

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

class CardTypeEnum(str, enum.Enum):
    debit = "DEBIT"
    credit = "CREDIT"

class CardStatusEnum(str, enum.Enum):
    active = "ACTIVE"
    blocked = "BLOCKED"

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
    iban = Column(String(26), unique=True, index=True, nullable=True, default=generate_iban)
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

class Card(Base):
    __tablename__ = "cards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=True) # Sadece banka kartları (debit) için
    
    card_number = Column(String(16), unique=True, index=True, nullable=False)
    card_holder_name = Column(String, nullable=False)
    expiry_date = Column(String(5), nullable=False) # MM/YY
    cvv = Column(String(3), nullable=False)
    
    card_type = Column(Enum(CardTypeEnum), nullable=False)
    status = Column(Enum(CardStatusEnum), default=CardStatusEnum.active, nullable=False)
    
    # Sadece kredi kartları için limit ve borç bilgisi
    credit_limit = Column(Numeric(precision=15, scale=2), default=0.00, nullable=False)
    current_debt = Column(Numeric(precision=15, scale=2), default=0.00, nullable=False)

    # Güvenlik Ayarları (User tarafından yönetilebilir)
    is_domestic_online = Column(String, default="TRUE", nullable=False) # Boolean as String for simplicity in some sqlite/pg setups
    is_international_online = Column(String, default="TRUE", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # İlişkiler
    owner = relationship("Customer")
    linked_account = relationship("Account")

class LimitRequestStatusEnum(str, enum.Enum):
    pending = "PENDING"
    approved = "APPROVED"
    rejected = "REJECTED"

class LimitRequest(Base):
    __tablename__ = "limit_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    card_id = Column(String, ForeignKey("cards.id"), nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    requested_limit = Column(Numeric(precision=15, scale=2), nullable=False)
    status = Column(Enum(LimitRequestStatusEnum), default=LimitRequestStatusEnum.pending, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # İlişkiler
    card = relationship("Card")
    customer = relationship("Customer")
