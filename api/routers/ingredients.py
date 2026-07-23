"""
api/routers/ingredients.py — Employee Ingredients CRUD
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user, require_admin, log_activity
from api.models import Ingredient, User
from api.schemas import IngredientCreate, IngredientResponse, IngredientUpdate

router = APIRouter()


@router.get("", response_model=List[IngredientResponse])
def list_ingredients(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [IngredientResponse.model_validate(i) for i in db.query(Ingredient).order_by(Ingredient.name).all()]


@router.post("", response_model=IngredientResponse, status_code=201)
def create_ingredient(
    body: IngredientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(Ingredient).filter(Ingredient.name == body.name).first():
        raise HTTPException(status_code=400, detail="Ingredient already exists")
    ing = Ingredient(**body.model_dump())
    db.add(ing)
    db.commit()
    db.refresh(ing)
    log_activity(db, current_user.id, "ingredient-create", {"name": body.name})
    db.commit()
    return IngredientResponse.model_validate(ing)


@router.get("/{ingredient_id}", response_model=IngredientResponse)
def get_ingredient(ingredient_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return IngredientResponse.model_validate(ing)


@router.put("/{ingredient_id}", response_model=IngredientResponse)
def update_ingredient(
    ingredient_id: int,
    body: IngredientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(ing, k, v)
    db.commit()
    db.refresh(ing)
    log_activity(db, current_user.id, "ingredient-update", {"id": ingredient_id})
    db.commit()
    return IngredientResponse.model_validate(ing)


@router.delete("/{ingredient_id}", status_code=204)
def delete_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    db.delete(ing)
    db.commit()
