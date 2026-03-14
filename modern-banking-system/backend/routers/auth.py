from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from passlib.context import CryptContext
from security import create_access_token, get_current_user, SECRET_KEY, ALGORITHM
from rate_limiter import limiter, LOGIN_LIMIT
import pyotp
from jose import jwt, JWTError

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
    # Kullanıcıyı veritabanında bul
    user = db.query(models.Customer).filter(models.Customer.username == form_data.username).first()
    
    # Kullanıcı yoksa veya şifre yanlışsa hata ver
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        audit_log = models.AuditLog(
            customer_id=user.id if user else None,
            action="LOGIN_FAILED",
            details="Incorrect username or password",
            ip_address=request.client.host if request.client else "Unknown"
        )
        db.add(audit_log)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Güvenlik sorusunu kontrol et
    if user.mothers_maiden_name.lower() != mothers_maiden_name.lower():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect security question answer (Mother's maiden name).",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2FA aktif mi kontrolü
    if user.is_two_factor_enabled == "TRUE":
        # Geçici token oluştur, bu token sadece /login/2fa için geçerli
        temp_token = create_access_token(data={"sub": user.id, "type": "2fa_temp"})
        return {"access_token": temp_token, "token_type": "bearer", "requires_2fa": True, "user_id": user.id, "role": user.role}

    # Token oluştur (2FA yoksa direkt giriş)
    audit_log = models.AuditLog(
        customer_id=user.id,
        action="LOGIN_SUCCESS",
        details="Direct login (No 2FA)",
        ip_address=request.client.host if request.client else "Unknown"
    )
    db.add(audit_log)
    db.commit()

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "requires_2fa": False, "user_id": user.id, "role": user.role}

@router.post("/login/2fa")
@limiter.limit(LOGIN_LIMIT)
def login_2fa(request: Request, body: schemas.TwoFactorLogin, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(body.temp_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "2fa_temp":
            raise HTTPException(status_code=401, detail="Invalid temporary token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid temporary token")
        
    user = db.query(models.Customer).filter(models.Customer.id == user_id).first()
    if not user or user.is_two_factor_enabled != "TRUE" or not user.two_factor_secret:
        raise HTTPException(status_code=400, detail="2FA is not enabled for this user")
        
    totp = pyotp.TOTP(user.two_factor_secret)
    if not totp.verify(body.otp_code):
        audit_log = models.AuditLog(
            customer_id=user.id,
            action="LOGIN_FAILED",
            details="Invalid 2FA OTP",
            ip_address=request.client.host if request.client else "Unknown"
        )
        db.add(audit_log)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid OTP code")
        
    # Asıl Access Token'ı ver
    audit_log = models.AuditLog(
        customer_id=user.id,
        action="LOGIN_SUCCESS",
        details="Logged in via 2FA",
        ip_address=request.client.host if request.client else "Unknown"
    )
    db.add(audit_log)
    db.commit()

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "requires_2fa": False, "user_id": user.id, "role": user.role}


@router.post("/2fa/setup", response_model=schemas.TwoFactorSetupResponse)
def setup_2fa(current_user: models.Customer = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.is_two_factor_enabled == "TRUE":
        raise HTTPException(status_code=400, detail="2FA is already enabled")
        
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    qr_url = totp.provisioning_uri(name=current_user.username, issuer_name="Rykard Bank")
    
    current_user.two_factor_secret = secret
    db.commit()
    
    return {"secret": secret, "qr_code_url": qr_url}


@router.post("/2fa/enable")
def enable_2fa(body: schemas.TwoFactorVerify, current_user: models.Customer = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.is_two_factor_enabled == "TRUE":
        raise HTTPException(status_code=400, detail="2FA is already enabled")
        
    if not current_user.two_factor_secret:
        raise HTTPException(status_code=400, detail="2FA setup not initialized. Call /2fa/setup first.")
        
    totp = pyotp.TOTP(current_user.two_factor_secret)
    if not totp.verify(body.token):
        raise HTTPException(status_code=400, detail="Invalid OTP code")
        
    current_user.is_two_factor_enabled = "TRUE"
    db.commit()
    
    return {"message": "2FA successfully enabled"}

@router.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password_card_verification(
    request: Request,
    body: schemas.ForgotPasswordCardRequest,
    db: Session = Depends(get_db)
):
    # 1. Look up the customer by username
    user = db.query(models.Customer).filter(models.Customer.username == body.username).first()
    
    if not user:
        # Prevent username enumeration - generic error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verfication failed. Please check your details."
        )
        
    # 2. Look up the card associated with this customer
    # Note: We match card_number, expiry_date, and cvv exactly.
    card = db.query(models.Card).filter(
        models.Card.customer_id == user.id,
        models.Card.card_number == body.card_number,
        models.Card.expiry_date == body.expiry_date,
        models.Card.cvv == body.cvv,
        models.Card.status == models.CardStatusEnum.active
    ).first()
    
    if not card:
        audit_log = models.AuditLog(
            customer_id=user.id,
            action="PASSWORD_RECOVERY_FAILED",
            details="Invalid card verification details provided",
            ip_address=request.client.host if request.client else "Unknown"
        )
        db.add(audit_log)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification failed. Please check your card details."
        )
        
    # 3. Validation successful, update the password
    user.password_hash = pwd_context.hash(body.new_password)
    
    audit_log = models.AuditLog(
        customer_id=user.id,
        action="PASSWORD_RECOVERY_SUCCESS",
        details="Password recovered via Card Verification",
        ip_address=request.client.host if request.client else "Unknown"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Password successfully reset. You can now login."}

