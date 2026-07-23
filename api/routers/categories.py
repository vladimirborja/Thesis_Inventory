"""
api/routers/categories.py
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user
from api.models import Category, User
from api.schemas import CategoryResponse

router = APIRouter()


@router.get("", response_model=List[CategoryResponse])
def list_categories(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [CategoryResponse.model_validate(c) for c in db.query(Category).order_by(Category.name).all()]
