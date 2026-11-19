"""Product catalog, reviews, and categories router using PostgreSQL / SQLAlchemy."""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Query, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductPublic,
    ReviewCreate,
    ReviewPublic,
    CategoryPublic,
)
from models.orm import Category
from services.product_service import product_service

router = APIRouter(tags=["Products & Reviews"])


@router.get(
    "/products",
    response_model=List[ProductPublic],
    summary="List and filter catalog products",
    status_code=status.HTTP_200_OK,
)
def get_products(
    category: Optional[str] = Query(None, description="Filter by category slug"),
    brand: Optional[str] = Query(None, description="Filter by brand name"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum sale price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum sale price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter only in-stock items"),
    search: Optional[str] = Query(None, description="Search query for title, brand, or description"),
    sort_by: Optional[str] = Query(
        None,
        description="Sorting option: price_asc, price_desc, rating, discount, name",
    ),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Pagination limit"),
    db: Session = Depends(get_db),
):
    """Retrieve catalog products with optional filtering, search, and sorting via DB."""
    return product_service.list_products(
        db=db,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        search=search,
        sort_by=sort_by,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/products/category/{category_slug}",
    summary="Category products compatibility endpoint",
    status_code=status.HTTP_200_OK,
)
def get_products_by_category(category_slug: str, db: Session = Depends(get_db)):
    """Compatibility route returning {'products': [...]}, matching techstore frontend expectations."""
    items = product_service.list_products(db=db, category=category_slug)
    return {"products": items, "total": len(items)}


@router.get(
    "/products/{product_id}",
    response_model=ProductPublic,
    summary="Get single product by ID",
    status_code=status.HTTP_200_OK,
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Retrieve detailed product specifications, calculated pricing, and reviews."""
    return product_service.get_product(db=db, product_id=product_id)


@router.post(
    "/products",
    response_model=ProductPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new catalog product",
)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Add a new product to the catalog."""
    return product_service.create_product(db=db, product_create=product)


@router.patch(
    "/products/{product_id}",
    response_model=ProductPublic,
    status_code=status.HTTP_200_OK,
    summary="Update product details or inventory stock",
)
def update_product(product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db)):
    """Update selected product properties (partial update with exclude_unset)."""
    return product_service.update_product(db=db, product_id=product_id, product_update=product_update)


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product from the catalog",
)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Remove a product by ID, checking for related orders (returns 409 if in orders)."""
    product_service.delete_product(db=db, product_id=product_id)
    return None


@router.post(
    "/products/{product_id}/reviews",
    response_model=ReviewPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Add a customer review and rating to a product",
)
def add_product_review(product_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    """Submits a review for a product and recalculates the average rating in DB."""
    return product_service.add_review(db=db, product_id=product_id, review_create=review)


@router.get(
    "/products/{product_id}/reviews",
    response_model=List[ReviewPublic],
    status_code=status.HTTP_200_OK,
    summary="List all reviews for a product",
)
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    """Returns all reviews submitted for a given product from DB."""
    return product_service.list_reviews(db=db, product_id=product_id)


@router.get(
    "/categories",
    summary="List all store categories from database table",
    status_code=status.HTTP_200_OK,
)
def get_categories(
    format: Optional[str] = Query(None, description="Optional format: 'list' for array of objects, default is dict"),
    db: Session = Depends(get_db),
):
    """Returns categories queried directly from the categories DB table."""
    categories = db.query(Category).order_by(Category.id.asc()).all()
    if format == "list":
        return [CategoryPublic.model_validate(c) for c in categories]
    return {c.slug: c.name for c in categories}
