"""
Pydantic schemas for Recommendations and Dashboard.
"""
from datetime import datetime
from pydantic import BaseModel


class Recommendation(BaseModel):
    id: str
    title: str
    description: str
    technology: str
    domain: str
    reason: str
    priority: str       # high / medium / low
    resource_type: str  # article / video / course / project
    resource_url: str | None = None
    estimated_hours: float | None = None


class RecommendationsResponse(BaseModel):
    weekly_focus: list[Recommendation]
    explore_next: list[Recommendation]
    quick_wins: list[Recommendation]
    behavioral_insights: list[str] = []
    generated_at: datetime


class DashboardStats(BaseModel):
    total_events: int
    events_this_week: int
    active_domains: int
    top_technology: str | None
    overall_skill_score: float
    learning_streak_days: int
    connected_sources: list[str]


class ActivityPoint(BaseModel):
    date: str
    event_count: int
    domains: list[str]


class DashboardResponse(BaseModel):
    user_id: int
    username: str
    stats: DashboardStats
    activity_last_30_days: list[ActivityPoint]
    top_skills: list[dict]
    recent_events: list[dict]
