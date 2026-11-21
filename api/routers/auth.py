"""
api/routers/auth.py — Login, Register, /me, profile + avatar
"""

import base64
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.database import get_db
from api.models import User
from api.schemas import (
    LoginRequest, LoginResponse, RegisterRequest, UserResponse, ProfileUpdateRequest,
)
from api.dependencies import (
    hash_password, verify_password,
    create_access_token, get_current_user, log_activity,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_MB = 3
# Serverless (Vercel) has a read-only filesystem — persist small avatars in Neon as data URLs.
MAX_INLINE_AVATAR_BYTES = 900_000
UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads" / "avatars"


def _cloudinary_configured() -> bool:
    name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    key = os.getenv("CLOUDINARY_API_KEY", "")
    secret = os.getenv("CLOUDINARY_API_SECRET", "")
    if not name or not key or not secret:
        return False
    placeholders = {"your_cloud_name", "your_api_key", "your_api_secret"}
    return name not in placeholders and key not in placeholders and secret not in placeholders


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
    log_activity(db, user.id, "login", {"email": user.email, "role": user.role})
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
        company_name=body.company_name or "Duque Food Products",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_activity(db, user.id, "register", {
        "email": user.email,
        "role": user.role,
        "company_name": user.company_name,
    })
    db.commit()

    token = create_access_token(user.id, user.role)
    return LoginResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_profile(
    body: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.name is not None:
        name = body.name.strip()
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
        current_user.name = name
    if body.company_name is not None:
        current_user.company_name = body.company_name.strip() or None

    log_activity(db, current_user.id, "profile-update", {
        "name": current_user.name,
        "company_name": current_user.company_name,
    })
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WebP images are allowed")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Image must be under {MAX_IMAGE_SIZE_MB}MB")

    avatar_url: str

    if _cloudinary_configured():
        import cloudinary
        import cloudinary.uploader
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
        )
        result = cloudinary.uploader.upload(
            contents,
            folder=f"ims/avatars/{current_user.id}",
            resource_type="image",
            overwrite=True,
        )
        avatar_url = result["secure_url"]
    else:
        # Prefer writing to disk in local/dev; fall back to inline data URL on
        # read-only hosts (Vercel) so profile photo upload never 500s.
        avatar_url = None
        try:
            UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
            ext = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
            }.get(file.content_type or "", ".jpg")
            filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
            dest = UPLOAD_ROOT / filename
            dest.write_bytes(contents)
            avatar_url = f"/api/auth/avatars/{filename}"
        except OSError:
            if len(contents) > MAX_INLINE_AVATAR_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail="Image is too large for serverless storage. Use a photo under 900KB, or configure Cloudinary.",
                )
            mime = file.content_type or "image/png"
            avatar_url = f"data:{mime};base64,{base64.b64encode(contents).decode('ascii')}"

    current_user.avatar_url = avatar_url
    log_activity(db, current_user.id, "avatar-upload", {
        "storage": "cloudinary" if _cloudinary_configured() else (
            "data-url" if avatar_url.startswith("data:") else "local"
        ),
    })
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/avatars/{filename}")
def serve_avatar(filename: str):
    """Serve locally stored avatars when Cloudinary is not configured."""
    safe = Path(filename).name
    path = UPLOAD_ROOT / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Avatar not found")
    return FileResponse(path)
