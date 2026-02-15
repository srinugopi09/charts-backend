"""Threads API — CRUD endpoints for conversation threads."""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, update, delete, func

from auth.dependencies import get_current_user_id
from db.connection import get_engine
from db.models import AgUiEvent, Thread

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/threads", tags=["threads"])

# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class ThreadCreate(BaseModel):
    thread_id: Optional[str] = None
    title: Optional[str] = None


class ThreadUpdate(BaseModel):
    title: str


class ThreadResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    created_at: str
    updated_at: str


class ThreadListResponse(BaseModel):
    threads: list[ThreadResponse]
    total: int


class MessageResponse(BaseModel):
    role: str
    content: str
    message_id: Optional[str] = None
    tool_call_name: Optional[str] = None
    tool_call_id: Optional[str] = None
    event_data: Optional[dict] = None


class MessagesResponse(BaseModel):
    thread_id: str
    messages: list[MessageResponse]


# ---------------------------------------------------------------------------
# Module-level reference to the ADK session service (set by main.py)
# ---------------------------------------------------------------------------

_session_service = None


def set_session_service(service):
    """Called once at startup from main.py to inject the session service."""
    global _session_service
    _session_service = service


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ThreadListResponse)
def list_threads(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List conversation threads for the current user."""
    engine = get_engine()
    with engine.connect() as conn:
        # Count
        count_stmt = select(func.count()).select_from(Thread.__table__).where(
            Thread.user_id == user_id
        )
        total = conn.execute(count_stmt).scalar() or 0

        # Fetch page
        stmt = (
            select(Thread.__table__)
            .where(Thread.user_id == user_id)
            .order_by(Thread.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = conn.execute(stmt).fetchall()

    threads = [
        ThreadResponse(
            id=str(r.id),
            user_id=r.user_id,
            title=r.title,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat(),
        )
        for r in rows
    ]
    return ThreadListResponse(threads=threads, total=total)


@router.post("", response_model=ThreadResponse, status_code=201)
def create_thread(
    body: ThreadCreate,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new conversation thread."""
    thread_id = uuid.UUID(body.thread_id) if body.thread_id else uuid.uuid4()
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(
            Thread.__table__.insert().values(
                id=thread_id,
                user_id=user_id,
                title=body.title,
            )
        )
        conn.commit()

        row = conn.execute(
            select(Thread.__table__).where(Thread.id == thread_id)
        ).fetchone()

    return ThreadResponse(
        id=str(row.id),
        user_id=row.user_id,
        title=row.title,
        created_at=row.created_at.isoformat(),
        updated_at=row.updated_at.isoformat(),
    )


@router.get("/{thread_id}", response_model=ThreadResponse)
def get_thread(
    thread_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a single thread by ID."""
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            select(Thread.__table__).where(
                Thread.id == uuid.UUID(thread_id),
                Thread.user_id == user_id,
            )
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Thread not found")

    return ThreadResponse(
        id=str(row.id),
        user_id=row.user_id,
        title=row.title,
        created_at=row.created_at.isoformat(),
        updated_at=row.updated_at.isoformat(),
    )


@router.patch("/{thread_id}", response_model=ThreadResponse)
def update_thread(
    thread_id: str,
    body: ThreadUpdate,
    user_id: str = Depends(get_current_user_id),
):
    """Update thread metadata (e.g. rename)."""
    engine = get_engine()
    tid = uuid.UUID(thread_id)
    with engine.connect() as conn:
        result = conn.execute(
            update(Thread.__table__)
            .where(Thread.id == tid, Thread.user_id == user_id)
            .values(title=body.title)
        )
        conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Thread not found")

        row = conn.execute(
            select(Thread.__table__).where(Thread.id == tid)
        ).fetchone()

    return ThreadResponse(
        id=str(row.id),
        user_id=row.user_id,
        title=row.title,
        created_at=row.created_at.isoformat(),
        updated_at=row.updated_at.isoformat(),
    )


@router.delete("/{thread_id}", status_code=204)
async def delete_thread(
    thread_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete a thread and its associated ADK session."""
    engine = get_engine()
    tid = uuid.UUID(thread_id)

    # Delete thread record
    with engine.connect() as conn:
        result = conn.execute(
            delete(Thread.__table__).where(
                Thread.id == tid, Thread.user_id == user_id
            )
        )
        conn.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Best-effort cleanup of the ADK session
    if _session_service is not None:
        try:
            await _session_service.delete_session(
                app_name="analytics_chatbot",
                user_id=user_id,
                session_id=thread_id,
            )
        except Exception:
            logger.warning(
                "Failed to delete ADK session for thread %s", thread_id)


@router.get("/{thread_id}/messages", response_model=MessagesResponse)
def get_thread_messages(
    thread_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Reconstruct conversation messages from persisted AG-UI events.

    Walks the stored events in order, concatenates text deltas into full
    messages, and returns tool call results with their original payloads.
    """
    engine = get_engine()
    tid = uuid.UUID(thread_id)

    # Verify thread ownership
    with engine.connect() as conn:
        owner = conn.execute(
            select(Thread.__table__.c.user_id).where(Thread.id == tid)
        ).scalar()

    if owner is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    if owner != user_id:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Fetch all events in order
    with engine.connect() as conn:
        rows = conn.execute(
            select(AgUiEvent.__table__)
            .where(AgUiEvent.thread_id == tid)
            .order_by(AgUiEvent.run_id, AgUiEvent.sequence)
        ).fetchall()

    # Reconstruct messages from streaming events
    messages: list[MessageResponse] = []
    text_buffers: dict[str, dict] = {}  # message_id -> {role, parts}
    tool_calls: dict[str, dict] = {}    # tool_call_id -> {name, args_parts}

    for row in rows:
        evt = row.event_data
        evt_type = row.event_type

        if evt_type == "USER_MESSAGE":
            messages.append(MessageResponse(
                role="user",
                content=evt.get("content", ""),
            ))

        elif evt_type == "TEXT_MESSAGE_START":
            mid = evt.get("messageId", "")
            text_buffers[mid] = {
                "role": evt.get("role", "assistant"),
                "parts": [],
            }

        elif evt_type == "TEXT_MESSAGE_CONTENT":
            mid = evt.get("messageId", "")
            if mid in text_buffers:
                text_buffers[mid]["parts"].append(evt.get("delta", ""))

        elif evt_type == "TEXT_MESSAGE_END":
            mid = evt.get("messageId", "")
            buf = text_buffers.pop(mid, None)
            if buf:
                messages.append(MessageResponse(
                    role=buf["role"],
                    content="".join(buf["parts"]),
                    message_id=mid,
                ))

        elif evt_type == "TOOL_CALL_START":
            tcid = evt.get("toolCallId", "")
            tool_calls[tcid] = {
                "name": evt.get("toolCallName", ""),
                "args_parts": [],
            }

        elif evt_type == "TOOL_CALL_ARGS":
            tcid = evt.get("toolCallId", "")
            if tcid in tool_calls:
                tool_calls[tcid]["args_parts"].append(evt.get("delta", ""))

        elif evt_type == "TOOL_CALL_END":
            tcid = evt.get("toolCallId", "")
            tc = tool_calls.pop(tcid, None)
            if tc:
                messages.append(MessageResponse(
                    role="assistant",
                    content="".join(tc["args_parts"]),
                    tool_call_name=tc["name"],
                    tool_call_id=tcid,
                ))

        elif evt_type == "TOOL_CALL_RESULT":
            messages.append(MessageResponse(
                role="tool",
                content=evt.get("content", ""),
                tool_call_id=evt.get("toolCallId", ""),
                event_data=evt,
            ))

    return MessagesResponse(thread_id=thread_id, messages=messages)
