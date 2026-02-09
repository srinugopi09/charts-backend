"""ADK orchestrator agent definition.

Creates the root Agent with Gemini LLM, system prompt, and all registered tools.
"""

from pathlib import Path

from google.adk.agents import Agent

from config.settings import get_settings
from tools.sql_tools import list_tables, describe_table, query_database
from tools.a2ui_tools import (
    generate_chart,
    generate_kpi_card,
    generate_data_table,
    generate_dashboard,
    generate_rag_indicator,
    generate_insight_card,
)

settings = get_settings()

# Load system prompt from file
_PROMPT_PATH = Path(__file__).parent / "prompts" / "orchestrator_system.txt"
_SYSTEM_PROMPT = _PROMPT_PATH.read_text()

# Create the orchestrator agent
orchestrator_agent = Agent(
    model=settings.gemini_model,
    name="analytics_orchestrator",
    instruction=_SYSTEM_PROMPT,
    tools=[
        list_tables,
        describe_table,
        query_database,
        generate_chart,
        generate_kpi_card,
        generate_data_table,
        generate_dashboard,
        generate_rag_indicator,
        generate_insight_card,
    ],
)
