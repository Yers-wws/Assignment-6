"""Promotions and discounts router using PostgreSQL / SQLAlchemy."""

from typing import Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.schemas import PromoValidateRequest, PromoValidateResponse
from models.orm import PromoCode
from services.promo_service import promo_service
from config import ACTIVE_PROMO_CODES

router = APIRouter(prefix="/promos", tags=["Promotions"])


@router.post(
    "/validate",
    response_model=PromoValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate promo code and calculate discount",
)
def validate_promo_code(payload: PromoValidateRequest, db: Session = Depends(get_db)):
    """
    Validates a promo code against store discounts in DB and returns potential savings.
    """
    return promo_service.validate_promo(db=db, code=payload.code, subtotal=payload.subtotal)


@router.get(
    "",
    response_model=Dict[str, float],
    status_code=status.HTTP_200_OK,
    summary="List available store promotion codes and discount rates",
)
def get_active_promotions(db: Session = Depends(get_db)):
    """Returns active promotional coupon codes from database."""
    promos = db.query(PromoCode).filter(PromoCode.is_active.is_(True)).all()
    if promos:
        return {p.code: (p.discount_percent or 0.0) for p in promos}
    return ACTIVE_PROMO_CODES
