"""
Recommendation engine — generates personalised learning recommendations
based on skill gaps,  weak areas, and learning momentum.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.skill_service import get_user_skills, get_skill_gaps

# Static resource database (in production: pull from a curated DB or AI call)
RESOURCE_DB: dict[str, list[dict]] = {
    "React": [
        {"title": "React Docs – Hooks Deep Dive", "url": "https://react.dev/reference/react/hooks", "type": "article", "hours": 2},
        {"title": "Jack Herrington – Advanced React", "url": "https://www.youtube.com/@jherr", "type": "video", "hours": 4},
    ],
    "TypeScript": [
        {"title": "TypeScript Handbook", "url": "https://www.typescriptlang.org/docs/", "type": "article", "hours": 3},
        {"title": "Matt Pocock – Total TypeScript", "url": "https://www.totaltypescript.com/", "type": "course", "hours": 10},
    ],
    "Python": [
        {"title": "Real Python – Advanced Python", "url": "https://realpython.com/", "type": "article", "hours": 2},
        {"title": "Fluent Python (Book)", "url": "https://www.oreilly.com/library/view/fluent-python-2nd/9781492056348/", "type": "article", "hours": 20},
    ],
    "FastAPI": [
        {"title": "FastAPI Official Tutorial", "url": "https://fastapi.tiangolo.com/tutorial/", "type": "article", "hours": 3},
        {"title": "Build Production FastAPI Apps", "url": "https://www.youtube.com/watch?v=0sOvCWFmrtA", "type": "video", "hours": 2},
    ],
    "Docker": [
        {"title": "Docker Getting Started", "url": "https://docs.docker.com/get-started/", "type": "article", "hours": 2},
        {"title": "TechWorld with Nana – Docker Crash Course", "url": "https://www.youtube.com/watch?v=3c-iBn73dDE", "type": "video", "hours": 3},
    ],
    "PostgreSQL": [
        {"title": "PostgreSQL Tutorial", "url": "https://www.postgresql.org/docs/current/tutorial.html", "type": "article", "hours": 3},
    ],
    "SQL": [
        {"title": "Mode Analytics SQL Tutorial", "url": "https://mode.com/sql-tutorial/", "type": "article", "hours": 4},
    ],
    "PyTorch": [
        {"title": "PyTorch Official Tutorials", "url": "https://pytorch.org/tutorials/", "type": "article", "hours": 6},
        {"title": "Andrej Karpathy – Neural Networks Zero to Hero", "url": "https://karpathy.ai/", "type": "video", "hours": 8},
    ],
}

DEFAULT_RESOURCES = [
    {"title": "Official Documentation", "url": None, "type": "article", "hours": 2},
    {"title": "YouTube Crash Course", "url": None, "type": "video", "hours": 1.5},
]


async def generate_recommendations(db: AsyncSession, user_id: int) -> dict:
    """
    Returns three recommendation buckets:
      - weekly_focus: top 2–3 gaps to tackle this week
      - explore_next: adjacent technologies to explore
      - quick_wins: techs with a small score boost potential
    """
    skills = await get_user_skills(db, user_id)
    gaps = await get_skill_gaps(db, user_id)

    weekly_focus = []
    explore_next = []
    quick_wins = []

    for gap in gaps[:3]:
        tech = gap["technology"]
        resources = RESOURCE_DB.get(tech, DEFAULT_RESOURCES)
        resource = resources[0] if resources else DEFAULT_RESOURCES[0]
        weekly_focus.append({
            "id": str(uuid.uuid4()),
            "title": f"Strengthen your {tech} skills",
            "description": f"Your {tech} score is {gap['current_score']:.0f}/100. Focus on: {', '.join(gap['recommended_topics'][:2])}.",
            "technology": tech,
            "domain": gap["domain"],
            "reason": f"Critical gap — {gap['priority']} priority",
            "priority": gap["priority"],
            "resource_type": resource["type"],
            "resource_url": resource.get("url"),
            "estimated_hours": resource.get("hours"),
        })

    # Explore: adjacent technologies in strong domains
    strong_domains = {s.domain for s in skills if s.score >= 50}
    ADJACENT: dict[str, list[str]] = {
        "Frontend": ["Testing (Jest/Vitest)", "Web Performance", "Accessibility"],
        "Backend": ["Message Queues", "gRPC", "Redis Caching"],
        "DevOps": ["SRE Practices", "GitOps", "Chaos Engineering"],
        "AI/ML": ["RAG Systems", "Model Serving", "MLOps"],
        "Data": ["Streaming (Kafka)", "Data Quality", "Feature Stores"],
    }
    for domain in strong_domains:
        for adj in ADJACENT.get(domain, [])[:2]:
            explore_next.append({
                "id": str(uuid.uuid4()),
                "title": f"Explore {adj}",
                "description": f"You're strong in {domain} — {adj} is a natural next step.",
                "technology": adj,
                "domain": domain,
                "reason": "Natural progression from current strength",
                "priority": "medium",
                "resource_type": "article",
                "resource_url": None,
                "estimated_hours": 3.0,
            })
        if len(explore_next) >= 3:
            break

    # Quick wins: skills between 30–55 (easy to level up)
    quick_win_skills = [s for s in skills if 30 <= s.score <= 55]
    for skill in quick_win_skills[:3]:
        resources = RESOURCE_DB.get(skill.technology, DEFAULT_RESOURCES)
        resource = resources[-1] if len(resources) > 1 else resources[0]
        quick_wins.append({
            "id": str(uuid.uuid4()),
            "title": f"Level up {skill.technology} to {skill.level} → Intermediate",
            "description": f"You're at {skill.score:.0f}/100. A focused 2–3 hour session can push you to the next level.",
            "technology": skill.technology,
            "domain": skill.domain,
            "reason": "Near a level threshold — quick win opportunity",
            "priority": "low",
            "resource_type": resource["type"],
            "resource_url": resource.get("url"),
            "estimated_hours": resource.get("hours"),
        })

    # Behavioral Insights (Product Differentiator)
    behavioral_insights = [
        "You learned Kafka but didn’t practice it. Try coding a project.",
        "You switched apps too frequently. Try focused sessions.",
        "Your Python activity is dropping. Revise key concepts."
    ]

    return {
        "weekly_focus": weekly_focus,
        "explore_next": explore_next,
        "quick_wins": quick_wins,
        "behavioral_insights": behavioral_insights,
        "generated_at": datetime.now(timezone.utc),
    }
