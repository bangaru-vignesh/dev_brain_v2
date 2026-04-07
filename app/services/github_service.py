"""
GitHub Service — Synchronizes repository activity and languages.
Analyzes repositories to create Knowledge Events.
"""
import httpx
from app.models.event import EventSource, EventDepth
from app.schemas.event import EventCreate
from app.services.event_service import create_event
from app.services.skill_service import rebuild_skill_graph

async def sync_github_repos(db, user_id, github_token):
    """
    Fetches user's public repos and creates knowledge events based on languages.
    """
    url = "https://api.github.com/user/repos?sort=updated&per_page=10"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to fetch GitHub data"}

        repos = response.json()
        events_created = 0

        for repo in repos:
            lang = repo.get("language")
            if not lang:
                continue
            
            # Map GitHub language to normalized topic
            # Note: In a full app, we would also fetch the specific languages breakdown
            
            event_data = EventCreate(
                topic=f"Repo: {repo['name']}",
                technology=lang,
                domain=_map_language_to_domain(lang),
                source=EventSource.GITHUB,
                source_url=repo["html_url"],
                source_title=repo["description"] or repo["name"],
                depth=EventDepth.INTERMEDIATE,
                confidence_score=0.9 # High confidence because it's actual code
            )

            await create_event(db, user_id, event_data)
            events_created += 1

        if events_created > 0:
            await rebuild_skill_graph(db, user_id)
            
        return {"events_synced": events_created}

def _map_language_to_domain(lang):
    mapping = {
        "Python": "Backend",
        "JavaScript": "Frontend",
        "TypeScript": "Frontend",
        "Go": "Backend",
        "Rust": "Backend",
        "HTML": "Frontend",
        "CSS": "Frontend",
        "Shell": "DevOps",
        "Jupyter Notebook": "AI/ML",
        "Java": "Backend",
        "Kotlin": "Mobile",
        "Swift": "Mobile"
    }
    return mapping.get(lang, "Engineering")


async def sync_github_events_from_api(db, user_id, github_username, github_token=None):
    """
    Step 2: Fetch events
    GET /users/{username}/events

    Step 3 & 4: Convert to DevBrain events and feed into pipeline
    """
    url = f"https://api.github.com/users/{github_username}/events"
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if github_token:
        headers["Authorization"] = f"token {github_token}"

    async with httpx.AsyncClient() as client:
        # Step 2: Fetch events
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to fetch GitHub events"}

        events = response.json()
        events_created = 0

        # Optional: update user's github username in DB
        from app.models.user import User
        from sqlalchemy import select
        res = await db.execute(select(User).where(User.id == user_id))
        user = res.scalar_one_or_none()
        if user and not user.github_username:
            user.github_username = github_username
            await db.commit()

        # Iterate over the events to parse out Commits, Repositories, Languages used, Contribution
        # The prompt says: "Track Commits, Repositories, Languages used, Contribution frequency"
        for evt in events:
            # We only care about PushEvent (Commits), CreateEvent, PublicEvent, PullRequestEvent, etc.
            evt_type = evt.get("type")
            repo_name = evt.get("repo", {}).get("name")
            created_at = evt.get("created_at")

            # Default attributes
            topic = f"GitHub Activity: {repo_name}"
            language = "Unknown"  # We'll deduce language later if needed (e.g. from repo data)
            concept = ""
            activity = "coding"
            
            # Step 3: Convert to DevBrain events
            if evt_type == "PushEvent":
                # User pushed commits
                commits = evt.get("payload", {}).get("commits", [])
                concept = f"Pushed {len(commits)} commits to {repo_name}"
                activity = "commit"
                
            elif evt_type == "PullRequestEvent":
                action = evt.get("payload", {}).get("action")
                concept = f"PR {action} on {repo_name}"
                activity = "pull_request"

            elif evt_type == "CreateEvent":
                ref_type = evt.get("payload", {}).get("ref_type")
                concept = f"Created {ref_type} on {repo_name}"
                activity = "create"

            else:
                continue # Skip uninteresting events

            # Create the KnowledgeEvent mapping
            # {
            #   "event_type": "coding",
            #   "source": "github",
            #   "repo": "devbrain",
            #   "language": "python",
            #   "activity": "commit",
            #   "timestamp": "..."
            # }
            
            # In a real app we'd query the repo for the main language. 
            # For this MVP simulation, we'll try to infer it or just leave it generic.
            if "python" in repo_name.lower() or "py" in repo_name.lower():
                language = "Python"
            elif "js" in repo_name.lower() or "react" in repo_name.lower() or "node" in repo_name.lower():
                language = "JavaScript"
            elif "go" in repo_name.lower():
                language = "Go"
            else:
                language = "Development"
                
            event_data = EventCreate(
                topic=topic,
                concept=concept,
                technology=language,
                domain=_map_language_to_domain(language),
                source=EventSource.GITHUB,
                source_url=f"https://github.com/{repo_name}",
                source_title=concept,
                depth=EventDepth.INTERMEDIATE,
                confidence_score=0.9, # High confidence for coding activity
                raw_data={
                    "event_type": "coding",
                    "repo": repo_name,
                    "activity": activity,
                    "github_event_id": evt.get("id"),
                    "timestamp": created_at
                }
            )

            # Step 4: Feed into your pipeline
            await create_event(db, user_id, event_data)
            events_created += 1

        if events_created > 0:
            # Trigger skill graph recalculation
            await rebuild_skill_graph(db, user_id)
            
        return {"events_synced": events_created}
