"""
Knowledge Events API — ingest raw learning signals.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.event import EventSource, EventDepth, ActivityType
from app.schemas.event import EventCreate, EventResponse, EventListResponse
from app.services.event_service import create_event, get_user_events
from app.services.skill_service import rebuild_skill_graph

from app.services.snowflake_service import snowflake_service

router = APIRouter()


@router.post("/", response_model=EventResponse, status_code=201)
async def ingest_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Ingest a single knowledge event and trigger skill graph rebuild.
    Also dispatches to Snowflake for long-term ETL.
    """
    event = await create_event(db, current_user.id, data)
    
    # Send to Snowflake (Direct Ingestion) asynchronously
    await snowflake_service.send_to_snowflake({
        "user_id": current_user.id,
        "source": data.source,
        "topic": data.topic,
        "technology": data.technology,
        "depth": data.depth,
        "url": data.source_url,
        "timestamp": event.created_at.isoformat() if event.created_at else None
    })

    # Trigger async skill recalculation inline for MVP
    await rebuild_skill_graph(db, current_user.id)
    return event


from app.services.classifier_service import classify_event

@router.post("/browser")
async def ingest_browser_history(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Specific endpoint for browser extensions.
    Categorizes the URL/Title, saves to local DB, and parallels to Snowflake.
    """
    url = payload.get("url", "")
    title = payload.get("title", "")
    
    # 1. Automatic Classification (Awaited because it calls AI API)
    analysis = await classify_event(url, title)
    
    # 1.5 Privacy & Waste Filter - Drop immediately if unrelated 
    if not analysis.get("is_relevant", True):
        return {
            "status": "ignored",
            "reason": "Not developer related, skipped for privacy.",
            "detected": analysis
        }

    
    # 2. Save to Local Knowledge Graph (so it shows on Dashboard)
    event_data = EventCreate(
        topic=analysis["topic"],
        technology=analysis["technology"],
        domain=analysis["domain"],
        source=EventSource.BROWSER,
        source_url=url,
        source_title=title,
        depth=analysis["depth"],
        confidence_score=analysis["confidence"],
        activity_type=analysis["activity_type"],
        engagement_score=analysis["engagement_score"]
    )
    
    local_event = await create_event(db, current_user.id, event_data)
    await rebuild_skill_graph(db, current_user.id)

    # 3. Dispatch to Snowflake for heavy ETL
    await snowflake_service.send_to_snowflake({
        "user_id": current_user.id,
        "source": "browser",
        "url": url,
        "title": title,
        "classification": analysis,
        "timestamp": local_event.created_at.isoformat()
    })
    
    return {
        "status": "categorized_and_ingested",
        "detected": analysis
    }


@router.post("/vscode")
async def ingest_vscode_activity(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Specific endpoint for VS Code active coding sessions."""
    language = payload.get("language", "Unknown")
    duration = payload.get("duration", 0)  # in seconds
    file_name = payload.get("file_name", "Unknown File")
    
    # Very minor sessions (under 1 minute) might be noisy
    if duration < 60:
        return {"status": "ignored", "reason": "session too short"}

    # Map language to Domain
    domain = _map_language_to_domain(language)
    
    # Prepare DevBrain event
    # A 2-hour session (7200s) has much higher engagement than a 5-minute session
    engagement = min(1.0, duration / 3600) 
    
    event_data = EventCreate(
        topic=f"Active Coding: {language}",
        concept=f"Worked on {file_name}",
        technology=language,
        domain=domain,
        source=EventSource.VSCODE,
        source_title=f"VS Code Session - {language}",
        depth=EventDepth.ADVANCED, # Coding is active learning
        confidence_score=1.0, # High confidence since it's hard instrumented time
        activity_type=ActivityType.CODING,
        engagement_score=engagement,
        raw_data=payload
    )

    local_event = await create_event(db, current_user.id, event_data)
    await rebuild_skill_graph(db, current_user.id)

    # Dispatch to Snowflake
    await snowflake_service.send_to_snowflake({
        "user_id": current_user.id,
        "source": "vscode",
        "language": language,
        "duration": duration,
        "timestamp": local_event.created_at.isoformat()
    })
    
    return {"status": "vscode_activity_ingested", "duration_recorded": duration}


@router.post("/desktop")
async def ingest_desktop_activity(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Specific endpoint for Desktop Agent activity."""
    app_name = payload.get("app", "Unknown")
    category = payload.get("category", "other")
    duration = payload.get("duration_seconds", 0)
    event_type = payload.get("event_type", "app_usage")

    if duration < 30:
        return {"status": "ignored", "reason": "session too short"}

    # Map category to ActivityType
    activity_map = {
        "coding": ActivityType.CODING,
        "learning": ActivityType.READING_DOCS,
        "distraction": ActivityType.BROWSING,
    }
    activity = activity_map.get(category, ActivityType.BROWSING)

    event_data = EventCreate(
        topic=f"Desktop: {app_name}",
        concept=f"Used {app_name} ({event_type})",
        technology=app_name,
        domain="Engineering" if category == "coding" else "General",
        source=EventSource.DESKTOP,
        source_title=f"Desktop Activity - {app_name}",
        depth=EventDepth.INTERMEDIATE,
        confidence_score=1.0,
        activity_type=activity,
        engagement_score=min(1.0, duration / 1800), # 30 min = full engagement
        raw_data=payload
    )

    local_event = await create_event(db, current_user.id, event_data)
    await rebuild_skill_graph(db, current_user.id)

    return {"status": "desktop_activity_ingested", "app": app_name}


def _map_language_to_domain(lang: str) -> str:
    lang = lang.lower()
    mapping = {
        "python": "Backend",
        "javascript": "Frontend",
        "typescript": "Frontend",
        "go": "Backend",
        "rust": "Backend",
        "html": "Frontend",
        "css": "Frontend",
        "shell": "DevOps",
        "java": "Backend",
        "c++": "Engineering",
        "c": "Engineering",
        "swift": "Mobile",
        "kotlin": "Mobile"
    }
    return mapping.get(lang.lower(), "Engineering")


@router.post("/github-webhook")
async def github_webhook(
    payload: dict,
):
    """Specific endpoint for GitHub webhooks."""
    # Note: In a real app, you'd match the GitHub user ID to your system user
    await snowflake_service.send_to_snowflake({
        "source": "github",
        "payload": payload,
        "type": "webhook"
    })
    return {"status": "webhook_received"}


from app.services.github_service import sync_github_repos

@router.post("/github/sync")
async def github_sync(
    token_payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Manually trigger a sync of GitHub repositories."""
    token = token_payload.get("token")
    if not token:
        return {"error": "GitHub token is required"}
    
    result = await sync_github_repos(db, current_user.id, token)
    return result


@router.get("/", response_model=EventListResponse)
async def list_events(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List the user's knowledge events, paginated."""
    total, items = await get_user_events(db, current_user.id, limit=limit, offset=offset)
    return EventListResponse(total=total, items=items)
