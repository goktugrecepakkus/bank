from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
import models
from passlib.context import CryptContext
from security import create_access_token
from rate_limiter import limiter, LOGIN_LIMIT

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/login")
@limiter.limit(LOGIN_LIMIT)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    mothers_maiden_name: str = Form(...),
    db: Session = Depends(get_db)
):
    # Kullanıcıyı veritabanında bul (OAuth2 Password flow'da username alanı emaili de temsil edebilir)
    user = db.query(models.Customer).filter(models.Customer.username == form_data.username).first()
    
    # Kullanıcı yoksa veya şifre yanlışsa hata ver
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Güvenlik sorusunu (anne kızlık soyadı) kontrol et
    if user.mothers_maiden_name.lower() != mothers_maiden_name.lower():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect security question answer (Mother's maiden name).",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Token oluştur
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "role": user.role}
