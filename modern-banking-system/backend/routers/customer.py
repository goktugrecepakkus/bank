from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from passlib.context import CryptContext

router = APIRouter(prefix="/customers", tags=["Customers"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    # Kullanıcı adı daha önce alınmış mı kontrol et
    db_customer = db.query(models.Customer).filter(models.Customer.username == customer.username).first()
    if db_customer:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Şifreyi hashle
    hashed_password = pwd_context.hash(customer.password)
    
    new_customer = models.Customer(
        username=customer.username,
        password_hash=hashed_password,
        role=customer.role
    )
    
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@router.get("/{customer_id}", response_model=schemas.CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
