"""
api/routers/auth.py — Login, Register, /me
Rate limited to 10 login attempts per minute per IP.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.database import get_db
from api.models import User
from api.schemas import LoginRequest, LoginResponse, RegisterRequest, UserResponse
from api.dependencies import (
    hash_password, verify_password,
    create_access_token, get_current_user, log_activity,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = create_access_token(user.id, user.role)
    log_activity(db, user.id, "login", {"email": user.email})
    db.commit()
    return LoginResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/register", response_model=LoginResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=body.name,
        email=body.email,
        password=hash_password(body.password),
        role=body.role,
        company_name=body.company_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_activity(db, user.id, "register", {"email": user.email, "role": user.role})
    db.commit()

    token = create_access_token(user.id, user.role)
    return LoginResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
