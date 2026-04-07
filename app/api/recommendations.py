"""
Recommendation API — personalised weekly learning recommendations.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.recommendation import RecommendationsResponse, Recommendation
from app.services.recommendation_service import generate_recommendations

router = APIRouter()


@router.get("/", response_model=RecommendationsResponse)
async def get_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns personalised learning recommendations in three buckets:
    - weekly_focus: highest-priority gaps to address this week
    - explore_next: adjacent skill expansion suggestions
    - quick_wins: near-threshold skills with easy improvement potential
    """
    data = await generate_recommendations(db, current_user.id)
    return RecommendationsResponse(
        weekly_focus=[Recommendation(**r) for r in data["weekly_focus"]],
        explore_next=[Recommendation(**r) for r in data["explore_next"]],
        quick_wins=[Recommendation(**r) for r in data["quick_wins"]],
        behavioral_insights=data.get("behavioral_insights", []),
        generated_at=data["generated_at"],
    )
