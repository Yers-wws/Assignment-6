"""Business logic for product catalog, stock updates, and customer reviews using PostgreSQL / SQLAlchemy."""

import json
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError

from models.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductPublic,
    ReviewCreate,
    ReviewPublic,
)
from models.orm import Product, Category, ProductReview, OrderItem


def calculate_sale_price(price: float, discount_pct: float) -> float:
    """Calculates discounted sale price rounded to 2 decimal places."""
    discounted = price * (1.0 - (discount_pct / 100.0))
    return round(discounted, 2)


def orm_to_product_public(p: Product) -> ProductPublic:
    """Serializes a Product ORM entity into ProductPublic Pydantic schema."""
    sale_price = calculate_sale_price(float(p.price), float(p.discount_percentage or 0.0))
    disc = float(p.discount_percentage or 0.0)

    # Parse images list
    images_list = []
    if p.images:
        try:
            images_list = json.loads(p.images) if isinstance(p.images, str) else list(p.images)
        except Exception:
            images_list = [p.images]

    # Convert reviews
    reviews_public = [
        ReviewPublic(
            id=r.id,
            reviewer_name=r.reviewer_name,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at),
        )
        for r in p.reviews
    ]

    cat_slug = p.category_rel.slug if p.category_rel else ""

    return ProductPublic(
        id=p.id,
        title=p.title,
        description=p.description or "",
        category=cat_slug,
        price=float(p.price),
        discount_percentage=disc,
        discountPercentage=disc,
        sale_price=sale_price,
        salePrice=sale_price,
        stock=p.stock,
        brand=p.brand,
        thumbnail=p.thumbnail,
        images=images_list,
        rating=float(p.rating),
        reviews_count=p.reviews_count,
        reviews=reviews_public,
        ram_gb=p.ram_gb,
        storage_gb=p.storage_gb,
        weight_kg=p.weight_kg,
        battery_mah=p.battery_mah,
        camera_mp=p.camera_mp,
        gaming_gpu=p.gaming_gpu,
        use_cases=p.use_cases,
    )


class ProductService:
    @staticmethod
    def list_products(
        db: Session,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[ProductPublic]:
        query = db.query(Product).options(joinedload(Product.category_rel), joinedload(Product.reviews))

        if category:
            cat_norm = category.strip().lower()
            query = query.join(Product.category_rel).filter(Category.slug.ilike(cat_norm))

        if brand:
            brand_norm = brand.strip().lower()
            query = query.filter(Product.brand.ilike(brand_norm))

        if in_stock is True:
            query = query.filter(Product.stock > 0)
        elif in_stock is False:
            query = query.filter(Product.stock == 0)

        if search:
            q = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    Product.title.ilike(q),
                    Product.description.ilike(q),
                    Product.brand.ilike(q),
                )
            )

        products_orm = query.all()
        public_items = [orm_to_product_public(p) for p in products_orm]

        # Price range filter based on calculated sale price
        if min_price is not None:
            public_items = [p for p in public_items if p.sale_price >= min_price]
        if max_price is not None:
            public_items = [p for p in public_items if p.sale_price <= max_price]

        # Sorting
        if sort_by == "price_asc":
            public_items.sort(key=lambda p: p.sale_price)
        elif sort_by == "price_desc":
            public_items.sort(key=lambda p: p.sale_price, reverse=True)
        elif sort_by == "rating":
            public_items.sort(key=lambda p: p.rating, reverse=True)
        elif sort_by == "discount":
            public_items.sort(key=lambda p: p.discount_percentage, reverse=True)
        elif sort_by == "name":
            public_items.sort(key=lambda p: p.title.lower())

        # Pagination
        if skip > 0:
            public_items = public_items[skip:]
        if limit is not None:
            public_items = public_items[:limit]

        return public_items

    @staticmethod
    def get_product(db: Session, product_id: int) -> ProductPublic:
        p = db.query(Product).options(joinedload(Product.category_rel), joinedload(Product.reviews)).filter(Product.id == product_id).first()
        if not p:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )
        return orm_to_product_public(p)

    @staticmethod
    def create_product(db: Session, product_create: ProductCreate) -> ProductPublic:
        # Resolve or create category
        cat_slug = product_create.category.strip().lower()
        cat = db.query(Category).filter(Category.slug == cat_slug).first()
        if not cat:
            cat = Category(slug=cat_slug, name=cat_slug.capitalize())
            db.add(cat)
            db.flush()

        data = product_create.model_dump()
        data.pop("category", None)
        images = data.pop("images", [])

        product = Product(
            category_id=cat.id,
            images=json.dumps(images) if isinstance(images, list) else str(images),
            rating=5.0,
            reviews_count=0,
            **data,
        )
        db.add(product)
        try:
            db.commit()
            db.refresh(product)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))

        return orm_to_product_public(product)

    @staticmethod
    def update_product(db: Session, product_id: int, product_update: ProductUpdate) -> ProductPublic:
        p = db.query(Product).options(joinedload(Product.category_rel), joinedload(Product.reviews)).filter(Product.id == product_id).first()
        if not p:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )

        update_data = product_update.model_dump(exclude_unset=True)

        if "category" in update_data:
            cat_slug = update_data.pop("category").strip().lower()
            cat = db.query(Category).filter(Category.slug == cat_slug).first()
            if not cat:
                cat = Category(slug=cat_slug, name=cat_slug.capitalize())
                db.add(cat)
                db.flush()
            p.category_id = cat.id

        if "images" in update_data:
            imgs = update_data.pop("images")
            p.images = json.dumps(imgs) if isinstance(imgs, list) else str(imgs)

        for field, val in update_data.items():
            setattr(p, field, val)

        try:
            db.commit()
            db.refresh(p)
        except IntegrityError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))

        return orm_to_product_public(p)

    @staticmethod
    def delete_product(db: Session, product_id: int) -> None:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )

        # Requirement 14 & 16: Check for related orders and return 409 Conflict
        has_orders = db.query(OrderItem).filter(OrderItem.product_id == product_id).first()
        if has_orders:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete product with ID {product_id} because it is referenced in existing order(s)",
            )

        try:
            db.delete(p)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete product with ID {product_id} due to existing database foreign key constraints",
            )

    @staticmethod
    def add_review(db: Session, product_id: int, review_create: ReviewCreate) -> ReviewPublic:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )

        review = ProductReview(
            product_id=product_id,
            reviewer_name=review_create.reviewer_name.strip(),
            rating=review_create.rating,
            comment=review_create.comment.strip(),
            created_at=datetime.now(timezone.utc),
        )
        db.add(review)
        db.flush()

        # Recalculate average rating and reviews count
        all_reviews = db.query(ProductReview).filter(ProductReview.product_id == product_id).all()
        ratings = [r.rating for r in all_reviews]
        p.rating = round(sum(ratings) / len(ratings), 1) if ratings else 5.0
        p.reviews_count = len(ratings)

        db.commit()
        db.refresh(review)

        return ReviewPublic(
            id=review.id,
            reviewer_name=review.reviewer_name,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at.isoformat(),
        )

    @staticmethod
    def list_reviews(db: Session, product_id: int) -> List[ReviewPublic]:
        p = db.query(Product).filter(Product.id == product_id).first()
        if not p:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )

        reviews = db.query(ProductReview).filter(ProductReview.product_id == product_id).order_by(ProductReview.id.asc()).all()
        return [
            ReviewPublic(
                id=r.id,
                reviewer_name=r.reviewer_name,
                rating=r.rating,
                comment=r.comment,
                created_at=r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at),
            )
            for r in reviews
        ]


product_service = ProductService()
