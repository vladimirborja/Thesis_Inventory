"""
api/routers/users.py — User management (Super Admin only)
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import require_super_admin
from api.models import User
from api.schemas import UserResponse, UserUpdateRole

router = APIRouter()


@router.get("", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_super_admin)):
    return [UserResponse.model_validate(u) for u in db.query(User).order_by(User.name).all()]


@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    body: UserUpdateRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    user.role = body.role
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    db.delete(user)
    db.commit()
