"""
Dashboard API — aggregated stats for the main UI view.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.recommendation import DashboardStats, DashboardResponse, ActivityPoint
from app.services.event_service import get_events_this_week, get_activity_last_30_days, get_user_events, get_today_events
from app.services.skill_service import get_user_skills

router = APIRouter()


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Aggregated dashboard view: stats, activity timeline, top skills."""
    total_events, recent_events = await get_user_events(db, current_user.id, limit=5)
    events_this_week = await get_events_this_week(db, current_user.id)
    skills = await get_user_skills(db, current_user.id)
    activity = await get_activity_last_30_days(db, current_user.id)

    active_domains = len({s.domain for s in skills})
    top_tech = skills[0].technology if skills else None
    overall_score = (sum(s.score for s in skills) / len(skills)) if skills else 0.0

    # Determine connected sources from events
    _, all_events = await get_user_events(db, current_user.id, limit=1000)
    connected_sources = list({e.source.value for e in all_events})

    stats = DashboardStats(
        total_events=total_events,
        events_this_week=events_this_week,
        active_domains=active_domains,
        top_technology=top_tech,
        overall_skill_score=round(overall_score, 1),
        learning_streak_days=_calculate_streak(activity),
        connected_sources=connected_sources,
    )

    top_skills = [
        {"technology": s.technology, "domain": s.domain, "score": round(s.score, 1), "level": s.level}
        for s in skills[:6]
    ]

    recent = [
        {
            "id": e.id,
            "topic": e.topic,
            "technology": e.technology,
            "domain": e.domain,
            "source": e.source.value,
            "created_at": e.created_at.isoformat(),
        }
        for e in recent_events
    ]

    return DashboardResponse(
        user_id=current_user.id,
        username=current_user.username,
        stats=stats,
        activity_last_30_days=[ActivityPoint(**a) for a in activity],
        top_skills=top_skills,
        recent_events=recent,
    )


@router.get("/daily-summary")
async def get_daily_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Answers: What did I actually do today? Focus vs Distraction vs Coding"""
    events = await get_today_events(db, current_user.id)
    
    summary = {
        "coding_time": 0.0,
        "learning_time": 0.0,
        "focus_time": 0.0,
        "distraction_time": 0.0,
        "top_activity": "None"
    }

    for event in events:
        raw = event.raw_data or {}
        event_type = raw.get("event_type", "")
        category = raw.get("category", "")
        source_val = event.source.value if hasattr(event.source, "value") else str(event.source)
        
        # Parse duration dynamically (Desktop sends duration_seconds, VSCode sends duration)
        # Default assume 10 mins (600s) if duration isn't explicitly tracked (e.g. Notion/Browser)
        dur_sec = float(raw.get("duration_seconds", raw.get("duration", 600)))
        dur_hours = dur_sec / 3600.0

        if event_type == "app_usage":
            if category == "coding":
                summary["coding_time"] += dur_hours
            elif category == "distraction":
                summary["distraction_time"] += dur_hours
        elif event_type == "focus_session":
            summary["focus_time"] += dur_hours
        elif source_val in ["browser", "notion"] or category == "learning":
            summary["learning_time"] += dur_hours
            
        # Fallback for native VSCode webhook events
        if event.activity_type and event.activity_type.value == "coding" and not event_type:
            summary["coding_time"] += dur_hours

    times = {
        "coding": summary["coding_time"],
        "learning": summary["learning_time"],
        "distraction": summary["distraction_time"]
    }
    if sum(times.values()) > 0:
        summary["top_activity"] = max(times, key=times.get)

    # Calculate Learning Health Score
    health_score = 50.0  # Base score
    # + Focus time
    health_score += summary["focus_time"] * 15
    # + Coding vs Learning balance
    if summary["coding_time"] > 0 and summary["learning_time"] > 0:
        ratio = min(summary["coding_time"], summary["learning_time"]) / max(summary["coding_time"], summary["learning_time"])
        health_score += ratio * 20
    elif summary["coding_time"] > 0 or summary["learning_time"] > 0:
        health_score += 10
    # - Low Distractions (penalize if present)
    health_score -= summary["distraction_time"] * 25
    
    summary["learning_health"] = int(max(0, min(100, health_score)))

    return {k: round(v, 2) if isinstance(v, float) else v for k, v in summary.items()}


@router.get("/top-topics")
async def get_top_topics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Answers: What did I learn today and how strong is the signal?"""
    events = await get_today_events(db, current_user.id)
    topic_scores = {}
    
    for event in events:
        topic = event.topic
        if not topic or topic == "Unknown":
            continue
            
        # Extract meaningful weight to aggregate a daily score.
        conf = getattr(event, 'confidence_score', 0.5)
        conf = 0.5 if conf is None else conf
        score_val = 10 * conf
        topic_scores[topic] = topic_scores.get(topic, 0) + score_val
        
    sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "topics": [{"topic": t, "score": round(s, 1)} for t, s in sorted_topics]
    }


def _calculate_streak(activity: list[dict]) -> int:
    """Count consecutive days with at least one event (working backwards from today)."""
    from datetime import datetime, timedelta, timezone

    if not activity:
        return 0

    days_with_events = {a["date"] for a in activity}
    streak = 0
    today = datetime.now(timezone.utc).date()

    for i in range(30):
        day_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if day_str in days_with_events:
            streak += 1
        else:
            break

    return streak
