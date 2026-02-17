"""PersistentADKAgent — subclass that persists AG-UI events to PostgreSQL.

Wraps ADKAgent.run() to intercept every AG-UI event and write it to the
``ag_ui_events`` table without blocking the SSE stream.
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor

from ag_ui.core import BaseEvent, RunAgentInput
from ag_ui_adk import ADKAgent

from sqlalchemy.dialects.postgresql import insert as pg_insert

from config.settings import get_settings
from db.connection import get_engine
from db.models import AgUiEvent, Thread

logger = logging.getLogger(__name__)

# Dedicated thread pool for DB writes, bounded to match the connection pool.
# This prevents the default executor (32+ threads) from exhausting the
# SQLAlchemy pool (pool_size + max_overflow = 15 by default).
_settings = get_settings()
_persist_executor = ThreadPoolExecutor(
    max_workers=_settings.db_pool_size + _settings.db_max_overflow,
    thread_name_prefix="persist-event",
)


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
    """Persist a single AG-UI event (runs in the persist executor)."""
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
            _persist_executor,
            _save_event_sync, thread_id, run_id, sequence, event, user_id,
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

    Persistence tasks run concurrently but are tracked and awaited after
    the SSE stream completes.  This ensures no events are silently lost
    on normal completion.  A class-level ``_inflight`` set enables
    graceful drain on shutdown.
    """

    # All in-flight persistence tasks across all runs, for shutdown drain.
    _inflight: set[asyncio.Task] = set()

    async def run(self, input_data: RunAgentInput):
        thread_id = input_data.thread_id
        run_id = input_data.run_id
        # Extract user_id from AG-UI state (injected by _extract_user_from_request)
        user_id = "anonymous"
        if isinstance(input_data.state, dict):
            user_id = input_data.state.get("_user_id", "anonymous")

        # Tasks created during this run — awaited after the stream ends.
        pending: list[asyncio.Task] = []

        # Persist the user message that triggered this run.
        if input_data.messages:
            for msg in reversed(input_data.messages):
                if getattr(msg, "role", None) == "user":
                    if isinstance(msg.content, str):
                        content = msg.content
                    elif isinstance(msg.content, list):
                        content = " ".join(
                            part.text for part in msg.content
                            if hasattr(part, "text")
                        )
                    else:
                        content = str(msg.content)
                    loop = asyncio.get_running_loop()
                    task = asyncio.create_task(
                        loop.run_in_executor(
                            _persist_executor,
                            _save_user_message_sync,
                            thread_id, run_id, user_id, content,
                        )
                    )
                    pending.append(task)
                    self._inflight.add(task)
                    task.add_done_callback(self._inflight.discard)
                    break

        sequence = 0

        try:
            async for event in super().run(input_data):
                task = asyncio.create_task(
                    _save_event_async(thread_id, run_id, sequence, event, user_id)
                )
                pending.append(task)
                self._inflight.add(task)
                task.add_done_callback(self._inflight.discard)
                sequence += 1
                yield event
        finally:
            # Wait for all persistence tasks from this run to finish.
            # Errors are already caught inside _save_event_async.
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)

    @classmethod
    async def drain(cls, timeout: float = 10.0) -> None:
        """Wait for all in-flight persistence tasks to complete.

        Called from the FastAPI shutdown handler to ensure no events
        are lost when the server stops.
        """
        if not cls._inflight:
            return
        logger.info("Draining %d in-flight persistence tasks...", len(cls._inflight))
        done, not_done = await asyncio.wait(cls._inflight, timeout=timeout)
        if not_done:
            logger.warning(
                "%d persistence tasks did not complete within %.1fs shutdown timeout",
                len(not_done), timeout,
            )
