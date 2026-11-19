"""Service for promotional codes and discounts using PostgreSQL / SQLAlchemy."""

from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from config import ACTIVE_PROMO_CODES
from models.schemas import PromoValidateResponse
from models.orm import PromoCode


class PromoService:
    @staticmethod
    def validate_promo(db: Session, code: str, subtotal: float = 0.0) -> PromoValidateResponse:
        normalized = (code or "").strip().upper()
        if not normalized:
            raise HTTPException(status_code=400, detail="Promo code cannot be empty")

        promo = db.query(PromoCode).filter(PromoCode.code == normalized, PromoCode.is_active.is_(True)).first()

        # Fallback to config if not found in db
        if not promo:
            if normalized in ACTIVE_PROMO_CODES:
                rate = ACTIVE_PROMO_CODES[normalized]
                discount_amount = round(subtotal * rate, 2)
                pct = round(rate * 100, 1)
                return PromoValidateResponse(
                    valid=True,
                    code=normalized,
                    discount_percentage=pct,
                    discount_amount=discount_amount,
                    message=f"Promo code applied: {pct}% off.",
                )

            return PromoValidateResponse(
                valid=False,
                code=normalized,
                discount_percentage=0.0,
                discount_amount=0.0,
                message=f"Promo code '{normalized}' is invalid or expired.",
            )

        rate = promo.discount_percent or 0.0
        if promo.fixed_amount:
            discount_amount = min(subtotal, float(promo.fixed_amount))
            pct = round((discount_amount / subtotal) * 100, 1) if subtotal > 0 else 0.0
        else:
            discount_amount = round(subtotal * rate, 2)
            pct = round(rate * 100, 1)

        return PromoValidateResponse(
            valid=True,
            code=normalized,
            discount_percentage=pct,
            discount_amount=discount_amount,
            message=f"Promo code applied: {pct}% off.",
        )


promo_service = PromoService()
