"""
api/routers/activity.py — Audit log (paginated, admin+ only)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import require_admin
from api.models import ActivityLog, User
from api.schemas import ActivityLogResponse

router = APIRouter()


@router.get("", response_model=List[ActivityLogResponse])
def list_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = (
        db.query(ActivityLog)
        .join(User, ActivityLog.user_id == User.id)
        .order_by(ActivityLog.created_at.desc())
    )
    if action_type:
        q = q.filter(ActivityLog.action_type == action_type)

    offset = (page - 1) * page_size
    logs = q.offset(offset).limit(page_size).all()

    result = []
    for log in logs:
        data = ActivityLogResponse.model_validate(log)
        data.user_name = log.user.name if log.user else None
        result.append(data)
    return result
