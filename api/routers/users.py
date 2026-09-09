"""
api/routers/users.py — User management (Admin + Super Admin)

Super Admin: full CRUD on all users
Admin: can view employees + toggle their transaction input permission
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import require_admin, require_super_admin, log_activity
from api.models import User
from api.schemas import UserResponse, UserUpdateRole, TogglePermissionRequest

router = APIRouter()


@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Super Admin: sees all users.
    Admin: sees employees only (cannot see other admins or super_admins).
    """
    if current_user.role == "super_admin":
        rows = db.query(User).order_by(User.name).all()
    else:
        # Admin sees only employees
        rows = db.query(User).filter(User.role == "employee").order_by(User.name).all()
    return [UserResponse.model_validate(u) for u in rows]


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
    log_activity(db, current_user.id, "user-role-update", {
        "target_user_id": user_id, "new_role": body.role,
    })
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.put("/{user_id}/permissions", response_model=UserResponse)
def update_user_permissions(
    user_id: int,
    body: TogglePermissionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Toggle an employee's can_input_transactions permission."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Admins can only manage employees, not other admins or super_admins
    if current_user.role == "admin" and user.role != "employee":
        raise HTTPException(status_code=403, detail="Admins can only manage employee permissions")

    user.can_input_transactions = body.can_input_transactions
    log_activity(db, current_user.id, "user-permission-update", {
        "target_user_id": user_id,
        "can_input_transactions": body.can_input_transactions,
    })
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
    log_activity(db, current_user.id, "user-delete", {
        "target_user_id": user_id, "email": user.email,
    })
    db.delete(user)
    db.commit()
