"""
PCI-DSS Card Data Encryption Module.
Fernet (AES-128-CBC + HMAC) ile kart numarası ve CVV şifreleme.
"""
import os
from cryptography.fernet import Fernet

# CARD_ENCRYPTION_KEY env variable'dan alınır
# Yoksa otomatik üretir ve uyarı verir (sadece development)
_key = os.getenv("CARD_ENCRYPTION_KEY")

if not _key:
    _key = Fernet.generate_key().decode()
    print(f"[SECURITY WARNING] No CARD_ENCRYPTION_KEY found! Auto-generated key: {_key}")
    print("[SECURITY WARNING] Set CARD_ENCRYPTION_KEY in .env or Vercel Dashboard to persist encrypted data!")

fernet = Fernet(_key.encode() if isinstance(_key, str) else _key)


def encrypt_card_field(value: str) -> str:
    """Kart alanını şifrele (card_number, cvv)"""
    return fernet.encrypt(value.encode()).decode()


def decrypt_card_field(encrypted_value: str) -> str:
    """Şifreli kart alanını çöz"""
    try:
        return fernet.decrypt(encrypted_value.encode()).decode()
    except Exception:
        # Eski (şifrelenmemiş) veri varsa olduğu gibi döndür
        return encrypted_value


def mask_card_number(card_number: str) -> str:
    """Kart numarasını maskele: **** **** **** 1234"""
    if len(card_number) >= 4:
        return "*" * (len(card_number) - 4) + card_number[-4:]
    return card_number
