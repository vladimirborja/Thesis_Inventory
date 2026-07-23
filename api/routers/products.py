"""
api/routers/products.py — CRUD + image upload
"""

import os
from typing import List, Optional

import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user, require_admin, log_activity
from api.models import Product, ProductImage, User
from api.schemas import ProductCreate, ProductResponse, ProductUpdate, ProductImageResponse

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE_MB   = 5


def _build_response(product: Product) -> ProductResponse:
    data = ProductResponse.model_validate(product)
    if product.category:
        data.category_name = product.category.name
    return data


@router.get("", response_model=List[ProductResponse])
def list_products(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    stock_status: Optional[str] = Query(None),  # all | low | out | instock
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Product)
    if search:
        term = f"%{search}%"
        q = q.filter(
            Product.name.ilike(term) | Product.sku.ilike(term) | Product.barcode.ilike(term)
        )
    if category_id:
        q = q.filter(Product.category_id == category_id)

    products = q.order_by(Product.name).all()

    if stock_status == "low":
        products = [p for p in products if 0 < p.quantity <= p.min_stock_level]
    elif stock_status == "out":
        products = [p for p in products if p.quantity == 0]
    elif stock_status == "instock":
        products = [p for p in products if p.quantity > p.min_stock_level]

    return [_build_response(p) for p in products]


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if db.query(Product).filter(Product.sku == body.sku).first():
        raise HTTPException(status_code=400, detail="SKU already exists")

    product = Product(**body.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)

    log_activity(db, current_user.id, "product-create", {"sku": body.sku, "name": body.name})
    db.commit()

    return _build_response(product)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _build_response(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    log_activity(db, current_user.id, "product-update", {"id": product_id})
    db.commit()
    return _build_response(product)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    log_activity(db, current_user.id, "product-delete", {"id": product_id})
    db.commit()


@router.post("/{product_id}/images", response_model=ProductImageResponse, status_code=201)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP images are allowed")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Image must be under {MAX_IMAGE_SIZE_MB}MB")

    result = cloudinary.uploader.upload(
        contents,
        folder=f"ims/products/{product_id}",
        resource_type="image",
    )

    img = ProductImage(
        product_id=product_id,
        image_url=result["secure_url"],
        public_id=result["public_id"],
    )
    db.add(img)
    db.commit()
    db.refresh(img)

    log_activity(db, current_user.id, "image-upload", {"product_id": product_id, "url": result["secure_url"]})
    db.commit()

    return ProductImageResponse.model_validate(img)
