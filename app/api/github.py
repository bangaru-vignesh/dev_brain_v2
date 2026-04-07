"""
GitHub Integration API - OAuth & Activity Fetcher.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.github_service import sync_github_events_from_api
from app.models.user import User

router = APIRouter()

@router.get("/login")
async def login_github(current_user: User = Depends(get_current_user)):
    """Step 1: OAuth - Redirect user to connect GitHub account."""
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub Client ID not configured.")
    # Add application state so we can identify the user during the callback
    state = f"{current_user.id}"
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&scope=user:email,repo"
        f"&state={state}"
    )
    return RedirectResponse(url=github_auth_url)


@router.get("/callback")
async def github_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Step 2 & 3 & 4: Callback to fetch events and convert to DevBrain events."""
    try:
        user_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Exchange code for access token
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, json=data, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to retrieve GitHub access token")
            
        token_data = resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token provided by GitHub")

        # Fetch GitHub User Info
        user_info_resp = await client.get(
            "https://api.github.com/user", 
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github.v3+json"}
        )
        if user_info_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub user info")
            
        github_user = user_info_resp.json()
        github_username = github_user.get("login")

    # Fetch events & convert to DevBrain events
    result = await sync_github_events_from_api(db, user_id, github_username, access_token)
    
    # Normally we would redirect to a frontend page with a success message
    # Here we can just return the result
    return {
        "status": "success",
        "message": f"Successfully connected GitHub account: {github_username}",
        "events_synced": result.get("events_synced", 0)
    }
