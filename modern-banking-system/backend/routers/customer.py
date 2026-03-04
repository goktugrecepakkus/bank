from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from passlib.context import CryptContext
from security import get_current_user

router = APIRouter(tags=["Customers"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/customers", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    print("======> CREATE CUSTOMER HIT")
    # Kullanıcı adı veya TC Kimlik numarası daha önce alınmış mı kontrol et
    db_customer = db.query(models.Customer).filter(models.Customer.username == customer.username).first()
    if db_customer:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    db_national_id = db.query(models.Customer).filter(models.Customer.national_id == customer.national_id).first()
    if db_national_id:
        raise HTTPException(status_code=400, detail="National ID already registered")
    
    # Şifreyi hashle
    hashed_password = pwd_context.hash(customer.password)
    
    new_customer = models.Customer(
        username=customer.username,
        password_hash=hashed_password,
        first_name=customer.first_name,
        last_name=customer.last_name,
        address=customer.address,
        phone_number=customer.phone_number,
        national_id=customer.national_id,
        mothers_maiden_name=customer.mothers_maiden_name,
        role=customer.role
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@router.get("/customers/{customer_id}", response_model=schemas.CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/customers/password")
def change_password(
    password_data: schemas.CustomerUpdatePassword,
    db: Session = Depends(get_db),
    current_user: models.Customer = Depends(get_current_user)
):
    """Kullanıcının şifresini güvenli bir şekilde günceller"""
    # 1. Eski şifreyi doğrula
    if not pwd_context.verify(password_data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect old password")
        
    # 2. Yeni şifre eskisinin aynısı olamaz
    if pwd_context.verify(password_data.new_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the old password")
        
    # 3. Şifreyi güncelle ve kaydet
    current_user.password_hash = pwd_context.hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}
