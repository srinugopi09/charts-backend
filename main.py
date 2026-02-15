import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from ag_ui.core import RunAgentInput
from ag_ui_adk import add_adk_fastapi_endpoint
from google.adk.sessions import DatabaseSessionService
from sqlalchemy import DateTime

from auth.dependencies import get_current_user_id
from config.settings import get_settings

# ---------------------------------------------------------------------------
# Patch: google-adk's PreciseTimestamp uses DateTime (no timezone) but inserts
# timezone-aware datetimes on PostgreSQL, which asyncpg rejects.  Fix by
# making the column type TIMESTAMP WITH TIME ZONE for PostgreSQL.
# ---------------------------------------------------------------------------
from google.adk.sessions.schemas.shared import PreciseTimestamp  # noqa: E402

_original_load_dialect_impl = PreciseTimestamp.load_dialect_impl


def _patched_load_dialect_impl(self, dialect):
    if dialect.name == "postgresql":
        return dialect.type_descriptor(DateTime(timezone=True))
    return _original_load_dialect_impl(self, dialect)


PreciseTimestamp.load_dialect_impl = _patched_load_dialect_impl

settings = get_settings()

# Export API key to os.environ so google-adk/genai SDK can find it
if settings.google_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)

from agents.orchestrator import orchestrator_agent  # noqa: E402
from agents.persistent_agent import PersistentADKAgent  # noqa: E402

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gemini_debug.log"),
    ],
)
logger = logging.getLogger(__name__)
# google-adk loggers use "google_adk" prefix (underscore, not dot)
logging.getLogger("google_adk.google.adk.models.google_llm").setLevel(logging.DEBUG)

app = FastAPI(title="Analytics Chatbot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Persistent session service (PostgreSQL)
# ---------------------------------------------------------------------------

session_service = DatabaseSessionService(db_url=settings.session_db_url_async)


# ---------------------------------------------------------------------------
# Auth helpers for AG-UI endpoint
# ---------------------------------------------------------------------------


async def _extract_user_from_request(
    request: Request, input_data: RunAgentInput
) -> dict:
    """Inject the authenticated user ID into AG-UI state."""
    user_id = get_current_user_id(request)
    return {"_user_id": user_id}


def _user_id_extractor(input_data: RunAgentInput) -> str:
    """Read user ID that was injected into state by the request extractor."""
    if isinstance(input_data.state, dict):
        return input_data.state.get("_user_id", "anonymous")
    return "anonymous"


# ---------------------------------------------------------------------------
# AG-UI endpoint
# ---------------------------------------------------------------------------

adk_agent_wrapper = PersistentADKAgent(
    adk_agent=orchestrator_agent,
    app_name="analytics_chatbot",
    user_id_extractor=_user_id_extractor,
    session_service=session_service,
)

add_adk_fastapi_endpoint(
    app,
    adk_agent_wrapper,
    path="/api/agent/run",
    extract_state_from_request=_extract_user_from_request,
)


# ---------------------------------------------------------------------------
# Threads API
# ---------------------------------------------------------------------------

from api.threads import router as threads_router, set_session_service  # noqa: E402

set_session_service(session_service)
app.include_router(threads_router)


# ---------------------------------------------------------------------------
# Startup: create application-owned tables
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def create_tables():
    from db.connection import get_engine
    from db.models import Base

    Base.metadata.create_all(bind=get_engine())
    logger.info("Application tables ensured (threads)")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    db_status = "disconnected"
    try:
        from sqlalchemy import text
        from db.connection import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        logger.warning("Health check: database unreachable")

    return {"status": "healthy", "database": db_status}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
