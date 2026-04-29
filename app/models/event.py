"""
KnowledgeEvent ORM model — represents a single learning signal.
"""
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class EventSource(str, enum.Enum):
    BROWSER = "browser"
    GITHUB = "github"
    YOUTUBE = "youtube"
    NOTES = "notes"
    MANUAL = "manual"
    VSCODE = "vscode"
    DESKTOP = "desktop"


class EventDepth(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ActivityType(str, enum.Enum):
    READING_DOCS = "reading_docs"
    WATCHING_VIDEO = "watching_video"
    CODING = "coding"
    BROWSING = "browsing"


class KnowledgeEvent(Base):
    __tablename__ = "knowledge_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # What was learned
    topic: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g. "Frontend", "DevOps"
    technology: Mapped[str] = mapped_column(String(100), nullable=True)          # e.g. "React", "Python"
    concept: Mapped[str] = mapped_column(String(200), nullable=True)              # e.g. "Hooks", "useEffect"

    # Source metadata
    source: Mapped[EventSource] = mapped_column(SAEnum(EventSource), default=EventSource.MANUAL)
    source_url: Mapped[str] = mapped_column(String(1024), nullable=True)
    source_title: Mapped[str] = mapped_column(String(500), nullable=True)

    # Depth / strength signal (0.0 → 1.0)
    depth: Mapped[EventDepth] = mapped_column(SAEnum(EventDepth), default=EventDepth.BEGINNER)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)

    # Activity learning signals
    activity_type: Mapped[ActivityType] = mapped_column(SAEnum(ActivityType), default=ActivityType.BROWSING)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.5)

    # Raw payload for extensibility
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="events")  # noqa: F821

    def __repr__(self) -> str:
        return f"<KnowledgeEvent id={self.id} topic={self.topic!r} source={self.source}>"
