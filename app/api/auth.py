from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, get_current_user
from app.core.config import get_settings
from app.models.user import User, AuditLog

router = APIRouter()
settings = get_settings()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    institution_name: str | None = None


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # Audit log
    log = AuditLog(
        user_id=user.id,
        action="LOGIN",
        resource_type="session",
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "institution_name": user.institution_name,
        },
    }


@router.post("/register", status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        institution_name=data.institution_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "message": "Account created"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "institution_name": current_user.institution_name,
    }


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = AuditLog(
        user_id=current_user.id,
        action="LOGOUT",
        resource_type="session",
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    db.commit()
    return {"message": "Logged out"}
