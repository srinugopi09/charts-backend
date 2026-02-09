import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint

from config.settings import get_settings

settings = get_settings()

# Export API key to os.environ so google-adk/genai SDK can find it
if settings.google_api_key:
    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)

from agents.orchestrator import orchestrator_agent  # noqa: E402

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Analytics Chatbot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# AG-UI endpoint
# ---------------------------------------------------------------------------

adk_agent_wrapper = ADKAgent(
    adk_agent=orchestrator_agent,
    app_name="analytics_chatbot",
    user_id="default_user",
)

add_adk_fastapi_endpoint(app, adk_agent_wrapper, path="/api/agent/run")


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
