"""
Agent Orchestrator — coordinates all travel planning agents.

Execution flow:
  Batch 1 (parallel): flight + hotel + weather + safety
  Batch 2 (parallel): activity + transport (need weather/flight data)
  Sequential: budget -> assembler

Uses asyncio.gather with return_exceptions=True for graceful failure handling.
"""
import asyncio
import logging
from typing import AsyncGenerator

from agents.state import TravelPlannerState
from agents.flight_agent import run_flight_agent
from agents.hotel_agent import run_hotel_agent
from agents.weather_agent import run_weather_agent
from agents.safety_agent import run_safety_agent
from agents.activity_agent import run_activity_agent
from agents.transport_agent import run_transport_agent
from agents.budget_agent import run_budget_agent
from agents.itinerary_assembler import run_assembler

logger = logging.getLogger(__name__)

BATCH_1_AGENTS = ["flight", "hotel", "weather", "safety"]
BATCH_2_AGENTS = ["activity", "transport"]


async def run_travel_planner(state: TravelPlannerState) -> TravelPlannerState:
    """
    Run all agents and assemble the itinerary.
    Uses asyncio.gather for parallel execution within batches.
    """
    logger.info(f"Agent orchestrator: selected_cities={state.get('selected_cities', [])}")
    state["agent_errors"] = state.get("agent_errors", [])
    state["progress_updates"] = state.get("progress_updates", [])

    # --- BATCH 1: Research (parallel) ---
    logger.info("Starting Batch 1: flight, hotel, weather, safety agents...")
    state["progress_updates"].append({"phase": "research", "message": "Researching flights, hotels, weather, and safety..."})

    results = await asyncio.gather(
        run_flight_agent(state),
        run_hotel_agent(state),
        run_weather_agent(state),
        run_safety_agent(state),
        return_exceptions=True,
    )

    agent_keys = ["flight_data", "hotel_data", "weather_data", "safety_data"]
    for i, (key, name) in enumerate(zip(agent_keys, BATCH_1_AGENTS)):
        if isinstance(results[i], Exception):
            logger.error(f"{name} agent failed: {results[i]}")
            state["agent_errors"].append(f"{name}: {str(results[i])}")
            state[key] = None
        else:
            state[key] = results[i]
            logger.info(f"{name} agent completed successfully")

    # --- BATCH 2: Planning (parallel, needs batch 1 data) ---
    logger.info("Starting Batch 2: activity, transport agents...")
    state["progress_updates"].append({"phase": "planning", "message": "Planning activities and transportation..."})

    results2 = await asyncio.gather(
        run_activity_agent(state),
        run_transport_agent(state),
        return_exceptions=True,
    )

    agent_keys2 = ["activity_data", "transport_data"]
    for i, (key, name) in enumerate(zip(agent_keys2, BATCH_2_AGENTS)):
        if isinstance(results2[i], Exception):
            logger.error(f"{name} agent failed: {results2[i]}")
            state["agent_errors"].append(f"{name}: {str(results2[i])}")
            state[key] = None
        else:
            state[key] = results2[i]
            logger.info(f"{name} agent completed successfully")

    # --- BUDGET OPTIMIZATION ---
    logger.info("Running budget agent...")
    state["progress_updates"].append({"phase": "budget", "message": "Analyzing budget..."})
    try:
        state["budget_analysis"] = await run_budget_agent(state)
        logger.info("Budget agent completed successfully")
    except Exception as e:
        logger.error(f"Budget agent failed: {e}")
        state["agent_errors"].append(f"budget: {str(e)}")
        state["budget_analysis"] = None

    # --- FINAL ASSEMBLY ---
    logger.info("Assembling itinerary...")
    state["progress_updates"].append({"phase": "assembling", "message": "Assembling your itinerary..."})
    try:
        state["itinerary"] = await run_assembler(state)
        if state["itinerary"]:
            logger.info("Itinerary assembled successfully")
        else:
            logger.error("Itinerary assembly returned None")
            state["agent_errors"].append("assembler: returned empty result")
    except Exception as e:
        logger.error(f"Itinerary assembly failed: {e}")
        state["agent_errors"].append(f"assembler: {str(e)}")
        state["itinerary"] = None

    return state


async def run_travel_planner_streaming(state: TravelPlannerState) -> AsyncGenerator[dict, None]:
    """
    Run all agents with SSE progress events.
    Yields dicts with {"event": "...", "data": {...}} for SSE streaming.
    """
    logger.info(f"Agent orchestrator (streaming): selected_cities={state.get('selected_cities', [])}")
    state["agent_errors"] = state.get("agent_errors", [])
    state["progress_updates"] = state.get("progress_updates", [])

    # --- BATCH 1 ---
    yield {"event": "agent_progress", "data": {"agent": "flight", "status": "working", "message": "Searching for flights..."}}
    yield {"event": "agent_progress", "data": {"agent": "hotel", "status": "working", "message": "Finding hotels..."}}
    yield {"event": "agent_progress", "data": {"agent": "weather", "status": "working", "message": "Checking weather..."}}
    yield {"event": "agent_progress", "data": {"agent": "safety", "status": "working", "message": "Reviewing safety..."}}

    results = await asyncio.gather(
        run_flight_agent(state),
        run_hotel_agent(state),
        run_weather_agent(state),
        run_safety_agent(state),
        return_exceptions=True,
    )

    agent_keys = ["flight_data", "hotel_data", "weather_data", "safety_data"]
    for i, (key, name) in enumerate(zip(agent_keys, BATCH_1_AGENTS)):
        if isinstance(results[i], Exception):
            logger.error(f"{name} agent failed: {results[i]}")
            state["agent_errors"].append(f"{name}: {str(results[i])}")
            state[key] = None
            yield {"event": "agent_progress", "data": {"agent": name, "status": "failed", "message": f"{name.title()} research encountered an issue"}}
        else:
            state[key] = results[i]
            yield {"event": "agent_progress", "data": {"agent": name, "status": "complete", "message": f"{name.title()} research complete"}}

    # --- BATCH 2 ---
    yield {"event": "agent_progress", "data": {"agent": "activity", "status": "working", "message": "Planning activities..."}}
    yield {"event": "agent_progress", "data": {"agent": "transport", "status": "working", "message": "Researching transportation..."}}

    results2 = await asyncio.gather(
        run_activity_agent(state),
        run_transport_agent(state),
        return_exceptions=True,
    )

    agent_keys2 = ["activity_data", "transport_data"]
    for i, (key, name) in enumerate(zip(agent_keys2, BATCH_2_AGENTS)):
        if isinstance(results2[i], Exception):
            logger.error(f"{name} agent failed: {results2[i]}")
            state["agent_errors"].append(f"{name}: {str(results2[i])}")
            state[key] = None
            yield {"event": "agent_progress", "data": {"agent": name, "status": "failed", "message": f"{name.title()} planning encountered an issue"}}
        else:
            state[key] = results2[i]
            yield {"event": "agent_progress", "data": {"agent": name, "status": "complete", "message": f"{name.title()} planning complete"}}

    # --- BUDGET ---
    yield {"event": "agent_progress", "data": {"agent": "budget", "status": "working", "message": "Optimizing budget..."}}
    try:
        state["budget_analysis"] = await run_budget_agent(state)
        yield {"event": "agent_progress", "data": {"agent": "budget", "status": "complete", "message": "Budget analysis complete"}}
    except Exception as e:
        logger.error(f"Budget agent failed: {e}")
        state["agent_errors"].append(f"budget: {str(e)}")
        state["budget_analysis"] = None
        yield {"event": "agent_progress", "data": {"agent": "budget", "status": "failed", "message": "Budget analysis encountered an issue"}}

    # --- ASSEMBLY ---
    yield {"event": "agent_progress", "data": {"agent": "assembler", "status": "working", "message": "Assembling your itinerary..."}}
    try:
        state["itinerary"] = await run_assembler(state)
        if state["itinerary"]:
            yield {"event": "agent_progress", "data": {"agent": "assembler", "status": "complete", "message": "Itinerary ready!"}}
            yield {"event": "itinerary", "data": state["itinerary"]}
        else:
            yield {"event": "agent_progress", "data": {"agent": "assembler", "status": "failed", "message": "Could not assemble itinerary"}}
    except Exception as e:
        logger.error(f"Itinerary assembly failed: {e}")
        state["agent_errors"].append(f"assembler: {str(e)}")
        state["itinerary"] = None
        yield {"event": "error", "data": {"message": "Failed to assemble itinerary. Please try again."}}
