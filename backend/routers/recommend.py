"""Advisor and product recommendation router."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.schemas import RecommendRequest, RecommendationItem
from services.recommend_service import recommend_service

router = APIRouter(tags=["Product Advisor"])


@router.post(
    "/recommend",
    response_model=List[RecommendationItem],
    status_code=status.HTTP_200_OK,
    summary="Get top 3 rule-based product recommendations",
)
def get_recommendations(request: RecommendRequest, db: Session = Depends(get_db)):
    """
    Evaluates catalog products against budget constraints, usage scenarios, and feature priorities,
    returning top 3 matching devices scored and annotated with Russian explanations.
    """
    return recommend_service.get_recommendations(db=db, request=request)
