"""Order placement and inventory checkout service using PostgreSQL / SQLAlchemy."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from config import FREE_SHIPPING_THRESHOLD, STANDARD_SHIPPING_FEE
from models.schemas import OrderCreate, OrderPublic, OrderItemPublic
from models.orm import Order, OrderItem, Product, PromoCode
from services.product_service import calculate_sale_price
from services.promo_service import promo_service


def orm_to_order_public(order: Order) -> OrderPublic:
    items_public = [
        OrderItemPublic(
            product_id=item.product_id,
            title=item.product.title if item.product else f"Product #{item.product_id}",
            price=float(item.product.price) if item.product else float(item.unit_price),
            sale_price=float(item.unit_price),
            quantity=item.quantity,
            subtotal=round(float(item.unit_price) * item.quantity, 2),
        )
        for item in order.items
    ]

    promo_code_str = order.promo_code_rel.code if order.promo_code_rel else None

    return OrderPublic(
        id=order.id,
        created_at=order.created_at.isoformat() if hasattr(order.created_at, "isoformat") else str(order.created_at),
        customer_name=order.customer_name,
        email=order.customer_email,
        shipping_address=order.shipping_address,
        items=items_public,
        subtotal=float(order.subtotal),
        discount=float(order.discount),
        shipping=float(order.shipping),
        total=float(order.total),
        promo_code=promo_code_str,
        status=order.status,
    )


class OrderService:
    @staticmethod
    def create_order(db: Session, order_create: OrderCreate) -> OrderPublic:
        """
        Executes transactional order checkout workflow:
        1. Validates product existence and stock availability.
        2. Applies optional promo code discounts.
        3. Computes delivery shipping fees.
        4. Atomically reserves/deducts inventory stock.
        5. Persists the created order and items.
        Rolls back all changes if any error occurs.
        """
        if not order_create.items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order items list cannot be empty")

        # Consolidate duplicate products in request
        consolidated_items: Dict[int, int] = {}
        for item in order_create.items:
            consolidated_items[item.product_id] = (
                consolidated_items.get(item.product_id, 0) + item.quantity
            )

        try:
            # Step 1: Pre-validation of products and stock
            order_items_data: List[Dict[str, Any]] = []
            subtotal = 0.0

            for pid, qty in consolidated_items.items():
                product = db.query(Product).filter(Product.id == pid).first()
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product with ID {pid} was not found in catalog",
                    )

                if product.stock < qty:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Insufficient stock for '{product.title}'. "
                            f"Requested quantity: {qty}, currently available: {product.stock}"
                        ),
                    )

                sale_p = calculate_sale_price(float(product.price), float(product.discount_percentage or 0.0))
                line_total = round(sale_p * qty, 2)
                subtotal += line_total

                order_items_data.append({
                    "product": product,
                    "product_id": pid,
                    "quantity": qty,
                    "unit_price": sale_p,
                })

            subtotal = round(subtotal, 2)

            # Step 2: Promo code validation & discount calculation
            discount = 0.0
            promo_code_id: Optional[int] = None
            if order_create.promo_code:
                promo_res = promo_service.validate_promo(db, order_create.promo_code, subtotal)
                if not promo_res.valid:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=promo_res.message,
                    )
                discount = promo_res.discount_amount
                # Look up promo record in DB if exists
                promo_rec = db.query(PromoCode).filter(PromoCode.code == promo_res.code).first()
                if promo_rec:
                    promo_code_id = promo_rec.id

            after_discount = max(0.0, subtotal - discount)

            # Step 3: Shipping fee calculation
            shipping = 0.0 if after_discount >= FREE_SHIPPING_THRESHOLD else STANDARD_SHIPPING_FEE
            total = round(after_discount + shipping, 2)

            # Step 4: Atomic stock deduction
            for item_data in order_items_data:
                item_data["product"].stock -= item_data["quantity"]

            # Step 5: Save order (with ID >= 1001)
            next_order_id = max((db.query(func.max(Order.id)).scalar() or 1000) + 1, 1001)
            order = Order(
                id=next_order_id,
                customer_name=order_create.customer_name.strip(),
                customer_email=order_create.email.strip().lower(),
                shipping_address=order_create.shipping_address.strip(),
                status="confirmed",
                promo_code_id=promo_code_id,
                subtotal=subtotal,
                discount=discount,
                shipping=shipping,
                total=total,
                created_at=datetime.now(timezone.utc),
            )
            db.add(order)
            db.flush()

            # Save order items
            for item_data in order_items_data:
                oi = OrderItem(
                    order_id=order.id,
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                    unit_price=item_data["unit_price"],
                )
                db.add(oi)

            db.commit()
            db.refresh(order)
            return orm_to_order_public(order)

        except (HTTPException, Exception) as e:
            db.rollback()
            raise e

    @staticmethod
    def list_orders(db: Session) -> List[OrderPublic]:
        orders = db.query(Order).options(
            joinedload(Order.items).joinedload(OrderItem.product),
            joinedload(Order.promo_code_rel),
        ).order_by(Order.id.desc()).all()
        return [orm_to_order_public(o) for o in orders]

    @staticmethod
    def get_order(db: Session, order_id: int) -> OrderPublic:
        order = db.query(Order).options(
            joinedload(Order.items).joinedload(OrderItem.product),
            joinedload(Order.promo_code_rel),
        ).filter(Order.id == order_id).first()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {order_id} not found",
            )
        return orm_to_order_public(order)

    @staticmethod
    def cancel_order(db: Session, order_id: int) -> OrderPublic:
        """
        Cancels an order and automatically restores stock to inventory in one transaction.
        """
        try:
            order = db.query(Order).options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.promo_code_rel),
            ).filter(Order.id == order_id).first()

            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Order with ID {order_id} not found",
                )

            if order.status == "cancelled":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Order {order_id} is already cancelled.",
                )

            # Restore stock
            for item in order.items:
                if item.product:
                    item.product.stock += item.quantity

            order.status = "cancelled"
            db.commit()
            db.refresh(order)
            return orm_to_order_public(order)
        except (HTTPException, Exception) as e:
            db.rollback()
            raise e


order_service = OrderService()
