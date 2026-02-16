"""PersistentADKAgent — subclass that persists AG-UI events to PostgreSQL.

Wraps ADKAgent.run() to intercept every AG-UI event and write it to the
``ag_ui_events`` table without blocking the SSE stream.
"""

import asyncio
import json
import logging

from ag_ui.core import BaseEvent, RunAgentInput
from ag_ui_adk import ADKAgent

from sqlalchemy.dialects.postgresql import insert as pg_insert

from db.connection import get_engine
from db.models import AgUiEvent, Thread

logger = logging.getLogger(__name__)


def _ensure_thread_exists(conn, thread_id: str, user_id: str) -> None:
    """Create the thread row if it doesn't exist yet (idempotent)."""
    stmt = pg_insert(Thread.__table__).values(
        id=thread_id,
        user_id=user_id,
    ).on_conflict_do_nothing(index_elements=["id"])
    conn.execute(stmt)


def _save_event_sync(
    thread_id: str, run_id: str, sequence: int, event: BaseEvent, user_id: str,
) -> None:
    """Persist a single AG-UI event (runs in a thread-pool executor)."""
    event_data = json.loads(event.model_dump_json(by_alias=True, exclude_none=True))
    event_type = event_data.get("type", "UNKNOWN")
    message_id = event_data.get("messageId") or event_data.get("toolCallId")

    engine = get_engine()
    with engine.connect() as conn:
        # Auto-create thread if frontend hasn't called POST /api/threads yet
        if sequence == 0:
            _ensure_thread_exists(conn, thread_id, user_id)

        conn.execute(
            AgUiEvent.__table__.insert().values(
                thread_id=thread_id,
                run_id=run_id,
                sequence=sequence,
                event_type=event_type,
                message_id=message_id,
                event_data=event_data,
            )
        )
        conn.commit()


def _save_user_message_sync(
    thread_id: str, run_id: str, user_id: str, content: str,
) -> None:
    """Persist the user message that triggered this run (sequence -1)."""
    engine = get_engine()
    with engine.connect() as conn:
        _ensure_thread_exists(conn, thread_id, user_id)
        conn.execute(
            AgUiEvent.__table__.insert().values(
                thread_id=thread_id,
                run_id=run_id,
                sequence=-1,
                event_type="USER_MESSAGE",
                message_id=None,
                event_data={"type": "USER_MESSAGE", "role": "user", "content": content},
            )
        )
        conn.commit()


async def _save_event_async(
    thread_id: str, run_id: str, sequence: int, event: BaseEvent, user_id: str,
) -> None:
    """Persist a single AG-UI event without blocking the event loop."""
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            None, _save_event_sync, thread_id, run_id, sequence, event, user_id,
        )
    except Exception:
        logger.warning(
            "Failed to persist AG-UI event seq=%d type=%s for thread=%s",
            sequence,
            getattr(event, "type", "?"),
            thread_id,
            exc_info=True,
        )


class PersistentADKAgent(ADKAgent):
    """ADKAgent that persists every AG-UI event to the ag_ui_events table.

    The persistence happens asynchronously (fire-and-forget) so the SSE
    stream is never blocked.  Failures are logged but do not interrupt
    the user's session.
    """

    async def run(self, input_data: RunAgentInput):
        thread_id = input_data.thread_id
        run_id = input_data.run_id
        # Extract user_id from AG-UI state (injected by _extract_user_from_request)
        user_id = "anonymous"
        if isinstance(input_data.state, dict):
            user_id = input_data.state.get("_user_id", "anonymous")

        # Persist the user message that triggered this run.
        # input_data.messages contains the full history; the last user
        # message is the one that triggered this run.
        if input_data.messages:
            for msg in reversed(input_data.messages):
                if getattr(msg, "role", None) == "user":
                    if isinstance(msg.content, str):
                        content = msg.content
                    elif isinstance(msg.content, list):
                        # Extract text from AG-UI content parts
                        content = " ".join(
                            part.text for part in msg.content
                            if hasattr(part, "text")
                        )
                    else:
                        content = str(msg.content)
                    asyncio.ensure_future(asyncio.get_running_loop().run_in_executor(
                        None, _save_user_message_sync,
                        thread_id, run_id, user_id, content,
                    ))
                    break

        sequence = 0

        async for event in super().run(input_data):
            asyncio.create_task(
                _save_event_async(thread_id, run_id, sequence, event, user_id)
            )
            sequence += 1
            yield event
