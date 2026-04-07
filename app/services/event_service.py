"""
Knowledge Event service — ingest and query learning events.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.event import KnowledgeEvent
from app.schemas.event import EventCreate


async def create_event(db: AsyncSession, user_id: int, data: EventCreate) -> KnowledgeEvent:
    event = KnowledgeEvent(
        user_id=user_id,
        topic=data.topic,
        domain=data.domain,
        technology=data.technology,
        concept=data.concept,
        source=data.source,
        source_url=data.source_url,
        source_title=data.source_title,
        depth=data.depth,
        confidence_score=data.confidence_score,
        raw_data=data.raw_data,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


async def get_user_events(
    db: AsyncSession, user_id: int, limit: int = 50, offset: int = 0
) -> tuple[int, list[KnowledgeEvent]]:
    count_q = await db.execute(
        select(func.count()).where(KnowledgeEvent.user_id == user_id)
    )
    total = count_q.scalar_one()

    result = await db.execute(
        select(KnowledgeEvent)
        .where(KnowledgeEvent.user_id == user_id)
        .order_by(desc(KnowledgeEvent.created_at))
        .limit(limit)
        .offset(offset)
    )
    return total, list(result.scalars().all())


async def get_events_this_week(db: AsyncSession, user_id: int) -> int:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(
        select(func.count())
        .where(KnowledgeEvent.user_id == user_id)
        .where(KnowledgeEvent.created_at >= week_ago)
    )
    return result.scalar_one()


async def get_today_events(db: AsyncSession, user_id: int) -> list[KnowledgeEvent]:
    """Returns all knowledge events ingested today (from midnight UTC)."""
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(KnowledgeEvent)
        .where(KnowledgeEvent.user_id == user_id)
        .where(KnowledgeEvent.created_at >= today)
        .order_by(KnowledgeEvent.created_at)
    )
    return list(result.scalars().all())


async def get_activity_last_30_days(db: AsyncSession, user_id: int) -> list[dict]:
    """Returns daily event counts over the last 30 days."""
    thirty_ago = datetime.now(timezone.utc) - timedelta(days=30)
    result = await db.execute(
        select(KnowledgeEvent)
        .where(KnowledgeEvent.user_id == user_id)
        .where(KnowledgeEvent.created_at >= thirty_ago)
        .order_by(KnowledgeEvent.created_at)
    )
    events = list(result.scalars().all())

    # Group by date
    by_date: dict[str, dict] = {}
    for ev in events:
        date_str = ev.created_at.strftime("%Y-%m-%d")
        if date_str not in by_date:
            by_date[date_str] = {"date": date_str, "event_count": 0, "domains": set()}
        by_date[date_str]["event_count"] += 1
        by_date[date_str]["domains"].add(ev.domain)

    # Convert sets to lists for JSON serialisation
    return [
        {"date": v["date"], "event_count": v["event_count"], "domains": list(v["domains"])}
        for v in sorted(by_date.values(), key=lambda x: x["date"])
    ]
