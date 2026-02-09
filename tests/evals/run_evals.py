#!/usr/bin/env python3
"""ADK agent evaluation runner.

Runs test cases against the real agent with Gemini and seeded database.
Each test case is run multiple times to account for LLM non-determinism.

Usage:
    uv run python tests/evals/run_evals.py --all
    uv run python tests/evals/run_evals.py --suite sql_accuracy
    uv run python tests/evals/run_evals.py --suite sql_accuracy --verbose
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def load_config() -> dict:
    config_path = Path(__file__).parent / "eval_config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_test_cases(suite_file: str) -> list[dict]:
    cases_path = Path(__file__).parent / suite_file
    with open(cases_path) as f:
        return yaml.safe_load(f)


async def run_single_case(case: dict, config: dict, verbose: bool = False) -> dict:
    """Run a single test case and return results."""
    # This is a placeholder for the actual ADK agent runner.
    # In a full implementation, this would:
    # 1. Create an ADK Runner with the orchestrator agent
    # 2. Send the input message(s) to the agent
    # 3. Collect all events from the agent response
    # 4. Evaluate the events against the expected criteria

    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from agents.orchestrator import orchestrator_agent

    session_service = InMemorySessionService()
    runner = Runner(
        agent=orchestrator_agent,
        app_name="eval_runner",
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name="eval_runner",
        user_id="eval_user",
    )

    # Handle multi-turn or single-turn
    turns = case.get("turns", [{"role": "user", "content": case.get("input", "")}])

    all_events = []
    for turn in turns:
        if turn["role"] != "user":
            continue

        content = types.Content(
            role="user",
            parts=[types.Part(text=turn["content"])],
        )

        events = []
        async for event in runner.run_async(
            user_id="eval_user",
            session_id=session.id,
            new_message=content,
        ):
            events.append(event)
            if verbose:
                print(f"  Event: {event.author} — {getattr(event, 'content', '')}")

        all_events.extend(events)

    # Extract tool calls and results from events
    tool_calls = []
    sql_queries = []
    viz_types = []

    for event in all_events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    tool_calls.append(part.function_call.name)
                    if part.function_call.name == "query_database":
                        args = part.function_call.args or {}
                        sql_queries.append(args.get("sql_query", ""))
                if hasattr(part, "function_response") and part.function_response:
                    resp = part.function_response.response or {}
                    if isinstance(resp, dict):
                        if resp.get("a2ui"):
                            msgs = resp.get("messages", [])
                            for msg in msgs:
                                uc = msg.get("updateComponents", {})
                                for comp in uc.get("components", []):
                                    if comp.get("component"):
                                        viz_types.append(comp["component"])

    return {
        "name": case.get("name", "unknown"),
        "tool_calls": tool_calls,
        "sql_queries": sql_queries,
        "viz_types": viz_types,
        "event_count": len(all_events),
    }


def evaluate_result(result: dict, expected: dict) -> tuple[bool, list[str]]:
    """Evaluate a test result against expected criteria. Returns (passed, reasons)."""
    failures = []

    # Check required tools
    if "required_tools" in expected:
        for tool in expected["required_tools"]:
            if tool not in result["tool_calls"]:
                failures.append(f"Missing required tool: {tool}")

    # Check forbidden tools
    if "forbidden_tools" in expected:
        for tool in expected["forbidden_tools"]:
            if tool in result["tool_calls"]:
                failures.append(f"Forbidden tool was called: {tool}")

    # Check tools_called (exact list)
    if "tools_called" in expected:
        for tool in expected["tools_called"]:
            if tool not in result["tool_calls"]:
                failures.append(f"Expected tool not called: {tool}")

    # Check SQL contains
    for key in ("sql_contains", "turn_2_sql_contains"):
        if key in expected:
            all_sql = " ".join(result["sql_queries"]).upper()
            for pattern in expected[key]:
                if pattern.upper() not in all_sql:
                    failures.append(f"SQL missing pattern: {pattern}")

    # Check viz type
    if "viz_type" in expected:
        accepted = expected["viz_type"]
        type_map = {"kpi": "KPICard", "dataTable": "DataTable", "dashboard": "CompositeDashboard"}
        found = any(
            vt.lower() in [a.lower() for a in accepted] or
            type_map.get(vt, vt).lower() in [a.lower() for a in accepted]
            for vt in result["viz_types"]
        )
        if not found and result["viz_types"]:
            failures.append(f"Wrong viz type: got {result['viz_types']}, expected one of {accepted}")

    return len(failures) == 0, failures


async def run_suite(suite_name: str, config: dict, verbose: bool = False):
    """Run a full evaluation suite."""
    suite_config = config["suites"][suite_name]
    cases = load_test_cases(suite_config["test_file"])
    eval_config = config["evaluation"]

    runs_per_case = eval_config.get("runs_per_case", 3)
    pass_threshold = eval_config.get("pass_threshold", 2)

    print(f"\n{'='*60}")
    print(f"Suite: {suite_name} — {suite_config['description']}")
    print(f"Cases: {len(cases)}, Runs/case: {runs_per_case}, Pass threshold: {pass_threshold}/{runs_per_case}")
    print(f"{'='*60}")

    suite_passed = 0
    suite_failed = 0

    for case in cases:
        case_name = case.get("name", "unknown")
        expected = case.get("expected", {})
        passes = 0
        all_failures = []

        for run_num in range(runs_per_case):
            try:
                result = await run_single_case(case, config, verbose)
                passed, failures = evaluate_result(result, expected)
                if passed:
                    passes += 1
                else:
                    all_failures.extend(failures)
            except Exception as e:
                all_failures.append(f"Run {run_num+1} exception: {str(e)}")

        case_passed = passes >= pass_threshold
        status = "PASS" if case_passed else "FAIL"
        print(f"  [{status}] {case_name} ({passes}/{runs_per_case} runs passed)")

        if not case_passed and all_failures:
            for f in set(all_failures):
                print(f"         - {f}")

        if case_passed:
            suite_passed += 1
        else:
            suite_failed += 1

    print(f"\nResults: {suite_passed} passed, {suite_failed} failed out of {len(cases)} cases")
    return suite_failed == 0


async def main():
    parser = argparse.ArgumentParser(description="Run ADK agent evaluations")
    parser.add_argument("--all", action="store_true", help="Run all evaluation suites")
    parser.add_argument("--suite", type=str, help="Run a specific suite (sql_accuracy, tool_selection, viz_selection, multi_turn)")
    parser.add_argument("--verbose", action="store_true", help="Show agent events during execution")
    parser.add_argument("--model", type=str, help="Override the Gemini model")
    args = parser.parse_args()

    config = load_config()

    if args.model:
        config["evaluation"]["model"] = args.model
        os.environ["GEMINI_MODEL"] = args.model

    if args.all:
        all_passed = True
        for suite_name in config["suites"]:
            passed = await run_suite(suite_name, config, args.verbose)
            if not passed:
                all_passed = False
        sys.exit(0 if all_passed else 1)

    elif args.suite:
        if args.suite not in config["suites"]:
            print(f"Unknown suite: {args.suite}")
            print(f"Available: {', '.join(config['suites'].keys())}")
            sys.exit(1)
        passed = await run_suite(args.suite, config, args.verbose)
        sys.exit(0 if passed else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
