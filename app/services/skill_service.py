"""
Skill Graph service — builds and queries user skill scores.

Scoring algorithm:
    score = min(100, Σ (confidence * depth_weight * recency_decay))

depth_weights: beginner=0.3, intermediate=0.6, advanced=1.0
recency_decay: events in last 7d → 1.0, 30d → 0.7, 90d → 0.4, older → 0.2
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.event import KnowledgeEvent, EventDepth, ActivityType, EventSource
from app.models.skill import UserSkill

SOURCE_WEIGHTS = {
    EventSource.NOTES: 1.0,
    EventSource.VSCODE: 0.8,
    EventSource.GITHUB: 0.8,
    EventSource.YOUTUBE: 0.6,
    EventSource.BROWSER: 0.5,
    EventSource.MANUAL: 0.4,
}

DEPTH_WEIGHTS = {
    EventDepth.BEGINNER: 0.8,
    EventDepth.INTERMEDIATE: 1.0,
    EventDepth.ADVANCED: 1.2,
}

ACTIVITY_WEIGHTS = {
    ActivityType.CODING: 1.5,
    ActivityType.WATCHING_VIDEO: 1.0,
    ActivityType.READING_DOCS: 0.8,
    ActivityType.BROWSING: 0.5,
}

LEVEL_THRESHOLDS = [
    (80, "Expert"),
    (60, "Advanced"),
    (40, "Intermediate"),
    (20, "Beginner"),
    (0, "Novice"),
]


def _recency_decay(event_date: datetime) -> float:
    # Ensure event_date is aware before subtraction
    if event_date.tzinfo is None:
        event_date = event_date.replace(tzinfo=timezone.utc)
    
    days_ago = (datetime.now(timezone.utc) - event_date).days
    if days_ago <= 7:
        return 1.0
    elif days_ago <= 30:
        return 0.7
    elif days_ago <= 90:
        return 0.4
    return 0.2


def _score_to_level(score: float) -> str:
    for threshold, label in LEVEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "Novice"


async def rebuild_skill_graph(db: AsyncSession, user_id: int) -> list[UserSkill]:
    """
    Recomputes all skill scores using hierarchical, deterministic, event-driven logic with diminishing returns.
    """
    from sqlalchemy import delete
    
    # 1. Fetch events chronologically
    result = await db.execute(
        select(KnowledgeEvent)
        .where(KnowledgeEvent.user_id == user_id)
        .order_by(KnowledgeEvent.created_at.asc())
    )
    events = list(result.scalars().all())

    # 2. Iterate and update Concept scores sequentially (diminishing returns)
    concept_data = {}
    seen_events = set()
    now = datetime.now(timezone.utc)
    
    for ev in events:
        domain = ev.domain or "General"
        tech = ev.technology or "General"
        
        # Missing Concept Fallback Handling
        concept = (ev.topic or "").strip()
        if not concept or concept.lower() in ("null", "none"):
            concept = "Fundamentals"
            
        key = (domain, tech, concept)
        
        # Event Duplication Prevention
        day_str = ev.created_at.strftime('%Y-%m-%d') if ev.created_at else ""
        dedup_key = (ev.source_url, day_str, ev.activity_type)
        if getattr(ev, 'source_url', None) and dedup_key in seen_events:
            continue
        if ev.source_url:
            seen_events.add(dedup_key)
        
        if key not in concept_data:
            concept_data[key] = {"score": 0.0, "events": 0, "last_activity": ev.created_at, "sources": set()}
            
        # Unbounded Difficulty Fix (cap to 1.3)
        raw_difficulty = 1.0
        if ev.depth == EventDepth.INTERMEDIATE: raw_difficulty = 1.1
        elif ev.depth == EventDepth.ADVANCED: raw_difficulty = 1.3
        difficulty_weight = min(1.3, raw_difficulty)
        
        # Fix Score Collapse: Use normalized factors centered near 1.0
        confidence = getattr(ev, 'confidence_score', 0.5)
        depth_w = DEPTH_WEIGHTS.get(ev.depth, 1.0)
        activity_w = ACTIVITY_WEIGHTS.get(getattr(ev, 'activity_type', ActivityType.BROWSING), 0.5)
        engagement_w = 0.5 + getattr(ev, 'engagement_score', 0.5)
        recency = _recency_decay(ev.created_at)
        source_w = SOURCE_WEIGHTS.get(getattr(ev, 'source', EventSource.BROWSER), 0.5)
        
        # Base event score shifted to balance out fractions
        event_score = 15.0 * confidence * depth_w * activity_w * engagement_w * recency * difficulty_weight * source_w
        
        # Apply diminishing returns logic at the concept level:
        old_score = concept_data[key]["score"]
        new_score = old_score + event_score * (1.0 - (old_score / 100.0))
        
        concept_data[key]["score"] = min(100.0, new_score)
        concept_data[key]["events"] += 1
        concept_data[key]["last_activity"] = max(concept_data[key]["last_activity"], ev.created_at)
        concept_data[key]["sources"].add(getattr(ev, 'source', EventSource.BROWSER))

    # Long-Term Skill Decay Execution & Cross-Signal Bonus
    for key, attrs in concept_data.items():
        # Cross Signal Bonus (Fuse multiple sources for high intelligence)
        source_count = len(attrs["sources"])
        bonus = 1.0
        if source_count == 2:
            bonus = 1.25
        elif source_count >= 3:
            bonus = 1.5
            
        attrs["score"] = min(100.0, attrs["score"] * bonus)

        days_inactive = (now - attrs["last_activity"]).days if attrs["last_activity"].tzinfo else (now.replace(tzinfo=None) - attrs["last_activity"]).days
        if days_inactive > 30:
            attrs["score"] *= (0.95 ** ((days_inactive - 30) / 30.0))

    # 3. Aggregate Technology scores
    tech_data = {}
    for (d, t, c), attrs in concept_data.items():
        key = (d, t)
        if key not in tech_data:
            tech_data[key] = {"concept_scores": [], "events": 0, "last_activity": attrs["last_activity"]}
            
        tech_data[key]["concept_scores"].append((attrs["score"], attrs["events"]))
        tech_data[key]["events"] += attrs["events"]
        tech_data[key]["last_activity"] = max(tech_data[key]["last_activity"], attrs["last_activity"])

    # 4. Aggregate Domain scores
    domain_data = {}
    for (d, t), attrs in tech_data.items():
        if d not in domain_data:
            domain_data[d] = {"tech_scores": [], "events": 0, "last_activity": attrs["last_activity"]}
        
        # Fix Equal Weighting: weight by sqrt(events)
        total_weight = 0.0
        weighted_sum = 0.0
        for c_score, c_events in attrs["concept_scores"]:
            w = (c_events ** 0.5)
            weighted_sum += c_score * w
            total_weight += w
        tech_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0
        
        attrs["score"] = tech_score  # Cache it
        
        domain_data[d]["tech_scores"].append((tech_score, attrs["events"]))
        domain_data[d]["events"] += attrs["events"]
        domain_data[d]["last_activity"] = max(domain_data[d]["last_activity"], attrs["last_activity"])

    for d, attrs in domain_data.items():
        total_weight = 0.0
        weighted_sum = 0.0
        for t_score, t_events in attrs["tech_scores"]:
            w = (t_events ** 0.5)
            weighted_sum += t_score * w
            total_weight += w
        attrs["score"] = (weighted_sum / total_weight) if total_weight > 0 else 0.0

    # 5. Clear old skills and insert the newly computed hierarchy
    await db.execute(delete(UserSkill).where(UserSkill.user_id == user_id))
    
    updated_skills = []
    
    # Save Domain-Level Nodes
    for d, info in domain_data.items():
        d_skill = UserSkill(
            user_id=user_id,
            domain=d,
            technology="ALL_DOMAIN", # Pseudo-technology for DB safety
            concept=None,
            score=min(100.0, info["score"]),
            level=_score_to_level(info["score"]),
            event_count=info["events"],
            last_activity=info["last_activity"]
        )
        db.add(d_skill)
        updated_skills.append(d_skill)

    # Save Technology-Level Nodes (concept=None)
    for (domain, tech), info in tech_data.items():
        t_score = info["score"]
        tech_skill = UserSkill(
            user_id=user_id,
            domain=domain,
            technology=tech,
            concept=None,
            score=min(100.0, t_score),
            level=_score_to_level(t_score),
            event_count=info["events"],
            last_activity=info["last_activity"]
        )
        db.add(tech_skill)
        updated_skills.append(tech_skill)
        
    # Save Concept-Level Nodes
    for (domain, tech, concept), info in concept_data.items():
        c_score = info["score"]
        db.add(UserSkill(
            user_id=user_id,
            domain=domain,
            technology=tech,
            concept=concept,
            score=min(100.0, c_score),
            level=_score_to_level(c_score),
            event_count=info["events"],
            last_activity=info["last_activity"]
        ))

    await db.flush()
    return updated_skills


async def get_user_skills(db: AsyncSession, user_id: int) -> list[UserSkill]:
    result = await db.execute(
        select(UserSkill)
        .where(UserSkill.user_id == user_id, UserSkill.concept.is_(None))
        .order_by(UserSkill.score.desc())
    )
    return list(result.scalars().all())


async def get_skill_gaps(db: AsyncSession, user_id: int) -> list[dict]:
    """
    Identifies weak spots: known domains where a key technology has low score.
    """
    skills = await get_user_skills(db, user_id)
    gaps = []

    # Domain → expected technologies mapping
    DOMAIN_TECH_MAP = {
        "Frontend": ["React", "TypeScript", "CSS", "Vue", "Next.js"],
        "Backend": ["Python", "FastAPI", "Django", "Node.js", "PostgreSQL"],
        "DevOps": ["Docker", "Kubernetes", "CI/CD", "Terraform", "AWS"],
        "Data": ["SQL", "Pandas", "Spark", "Airflow", "dbt"],
        "AI/ML": ["PyTorch", "TensorFlow", "scikit-learn", "LangChain", "Transformers"],
        "Mobile": ["React Native", "Swift", "Kotlin", "Flutter"],
    }

    known_tech = {(s.domain, s.technology): s.score for s in skills}
    known_domains = {s.domain for s in skills}

    for domain in known_domains:
        expected = DOMAIN_TECH_MAP.get(domain, [])
        for tech in expected:
            score = known_tech.get((domain, tech), 0.0)
            if score < 40:
                priority = "high" if score < 10 else "medium" if score < 25 else "low"
                gaps.append({
                    "technology": tech,
                    "domain": domain,
                    "current_score": score,
                    "recommended_topics": _get_recommended_topics(tech),
                    "priority": priority,
                })

    return sorted(gaps, key=lambda g: g["current_score"])


def _get_recommended_topics(tech: str) -> list[str]:
    TOPIC_MAP = {
        "React": ["Hooks", "Context", "Server Components", "React Query"],
        "TypeScript": ["Generics", "Type Guards", "Utility Types", "Mapped Types"],
        "Python": ["Async/Await", "Decorators", "Type Hints", "Generators"],
        "FastAPI": ["Dependency Injection", "Background Tasks", "WebSockets", "Middleware"],
        "Docker": ["Multi-stage builds", "Compose", "Networking", "Volumes"],
        "PostgreSQL": ["Indexes", "Transactions", "Query Planner", "Partitioning"],
        "SQL": ["JOINs", "Window Functions", "CTEs", "Indexing"],
        "PyTorch": ["Autograd", "Custom Layers", "DataLoader", "CUDA"],
    }
    return TOPIC_MAP.get(tech, ["Fundamentals", "Best Practices", "Advanced Patterns"])
