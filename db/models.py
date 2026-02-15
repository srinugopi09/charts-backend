"""SQLAlchemy ORM models for application-owned tables."""

import uuid

from sqlalchemy import (
    BigInteger, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Thread(Base):
    """A conversation thread owned by a user.

    The ``id`` matches the AG-UI ``threadId`` that the frontend sends on
    every ``/api/agent/run`` request.  Storing it server-side lets us
    list, rename, and delete conversations per user.
    """

    __tablename__ = "threads"

    id = Column(PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AgUiEvent(Base):
    """A persisted AG-UI protocol event.

    Each row captures one SSE event exactly as streamed to the frontend.
    Events are grouped by ``run_id`` and ordered by ``sequence`` within a run.
    """

    __tablename__ = "ag_ui_events"
    __table_args__ = (
        UniqueConstraint("thread_id", "run_id", "sequence", name="uq_ag_ui_event_ordering"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    thread_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id = Column(String, nullable=False)
    sequence = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    message_id = Column(String(100), nullable=True)
    event_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
