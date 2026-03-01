import os
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import database

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_database():
    models.Base.metadata.create_all(bind=database.engine)
    db: Session = SessionLocal()
    
    # Veritabanında zaten admin var mı kontrol et
    admin_exists = db.query(models.Customer).filter(models.Customer.username == "admin").first()
    if admin_exists:
        print("Test verileri zaten yüklenmiş.")
        db.close()
        return

    print("--- Örnek Test Verileri ve Hesaplar Oluşturuluyor ---")
    
    # 1. Admin Kullanıcısı
    admin = models.Customer(
        username="admin",
        password_hash=pwd_context.hash("admin123"),
        first_name="System",
        last_name="Administrator",
        address="Bank HQ",
        phone_number="0000000000",
        national_id="00000000000",
        role=models.RoleEnum.admin
    )
    db.add(admin)

    # 2. Test Müşterisi
    customer1 = models.Customer(
        username="johndoe",
        password_hash=pwd_context.hash("pass1234"),
        first_name="John",
        last_name="Doe",
        address="123 Bank Street",
        phone_number="5551234567",
        national_id="12345678901",
        role=models.RoleEnum.customer
    )
    db.add(customer1)
    
    db.commit()
    db.refresh(customer1)
    
    # 3. Test Müşterisi İçin Hesap Aç ve İçine Para Koy (Deposit)
    account1 = models.Account(
        customer_id=customer1.id,
        account_type=models.AccountTypeEnum.checking,
        balance=5000.00
    )
    db.add(account1)
    db.commit()
    db.refresh(account1)
    
    # Hesaba konulan paranın Ledger (Defter) kaydını oluştur
    ledger_entry = models.Ledger(
        to_account_id=account1.id,
        amount=5000.00,
        transaction_type=models.TransactionTypeEnum.deposit
    )
    db.add(ledger_entry)
    db.commit()
    
    # 4. İkinci Bir Hesap Daha Aç (Para Gönderebilmek için)
    account2 = models.Account(
        customer_id=customer1.id, # Aslında başka müşteri de olabilir
        account_type=models.AccountTypeEnum.savings,
        balance=0.00
    )
    db.add(account2)
    db.commit()

    print(f"SUCCESS: johndoe kullanıcısı oluşturuldu. Şifre: pass1234")
    print(f"SUCCESS: johndoe'nun Ana Hesabı (ID): {account1.id} Bakiye: 5000")
    print(f"SUCCESS: johndoe'nun Yan Hesabı (ID): {account2.id} Bakiye: 0")

    db.close()

if __name__ == "__main__":
    seed_database()
