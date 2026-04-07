"""
DevBrain - Personal Learning OS for Developers
FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, skills, events, recommendations, dashboard, analytics, chat, github
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    print("   [Boot] Initializing Database...")
    await init_db()
    
    # Auto-seed a user for the user to login immediately
    print("   [Boot] Checking if test user exists...")
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from app.core.security import hash_password
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.email == "testuser@devbrain.dev"))
        if not res.scalar_one_or_none():
            print("   [Boot] Creating default user: testuser@devbrain.dev / password123")
            user = User(
                email="testuser@devbrain.dev",
                username="testuser",
                hashed_password=hash_password("password123"),
                is_active=True,
                is_verified=True
            )
            session.add(user)
            await session.commit()
            print("   [Boot] User created successfully.")
        else:
            print("   [Boot] Test user already exists.")
            
    yield


app = FastAPI(
    title="DevBrain API",
    description="Personal Learning OS for Developers — track, graph, and grow your skills automatically.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router,            prefix="/api/auth",            tags=["Authentication"])
app.include_router(events.router,          prefix="/api/events",          tags=["Knowledge Events"])
app.include_router(skills.router,          prefix="/api/skills",          tags=["Skill Graph"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(dashboard.router,       prefix="/api/dashboard",       tags=["Dashboard"])
app.include_router(analytics.router,       prefix="/api/analytics",       tags=["Analytics - Snowflake"])
app.include_router(chat.router,            prefix="/api/chat",            tags=["AI Chatbot"])
app.include_router(github.router,          prefix="/api/github",          tags=["GitHub Integration"])



@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "DevBrain API", "version": "1.0.0"}
