"""SQLAlchemy ORM models for Voltix TechStore."""

from datetime import datetime, timezone


def get_utc_now():
    return datetime.now(timezone.utc)
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)

    products = relationship("Product", back_populates="category_rel", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False, index=True)
    brand = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    rating = Column(Float, default=5.0, nullable=False)
    reviews_count = Column(Integer, default=0, nullable=False)
    discount_percentage = Column(Float, default=0.0, nullable=False)
    thumbnail = Column(String(500), nullable=True)
    images = Column(Text, nullable=True, default="[]")  # JSON string or comma-separated list of image URLs
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)

    # Advisor / Technical characteristics (demo data where applicable)
    ram_gb = Column(Integer, nullable=True)
    storage_gb = Column(Integer, nullable=True)
    weight_kg = Column(Float, nullable=True)
    battery_mah = Column(Integer, nullable=True)
    camera_mp = Column(Integer, nullable=True)
    gaming_gpu = Column(Boolean, default=False, nullable=True)
    use_cases = Column(String(255), nullable=True)  # Comma-separated: "office,study,gaming"

    # Relationships
    category_rel = relationship("Category", back_populates="products")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product", passive_deletes=False)

    __table_args__ = (
        CheckConstraint("price > 0", name="check_product_price_positive"),
        CheckConstraint("stock >= 0", name="check_product_stock_non_negative"),
        CheckConstraint("discount_percentage >= 0 AND discount_percentage <= 90", name="check_product_discount_range"),
    )


class ProductReview(Base):
    __tablename__ = "product_reviews"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    reviewer_name = Column(String(100), default="Customer", nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    product = relationship("Product", back_populates="reviews")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_review_rating_range"),
    )


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    discount_percent = Column(Float, nullable=True)  # e.g., 0.10 for 10%
    fixed_amount = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    orders = relationship("Order", back_populates="promo_code_rel")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), default="Customer", nullable=False)
    customer_email = Column(String(255), nullable=False, index=True)
    shipping_address = Column(String(255), default="Store Pickup", nullable=False)
    status = Column(String(50), default="confirmed", nullable=False)
    promo_code_id = Column(Integer, ForeignKey("promo_codes.id", ondelete="SET NULL"), nullable=True)
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), default=0.0, nullable=False)
    shipping = Column(Numeric(10, 2), default=0.0, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    promo_code_rel = relationship("PromoCode", back_populates="orders")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_order_item_quantity_positive"),
    )
