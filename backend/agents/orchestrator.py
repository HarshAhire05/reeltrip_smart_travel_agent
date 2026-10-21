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


async def run_travel_planner_streaming(
    state: TravelPlannerState,
    skip_agents: list[str] | None = None
) -> AsyncGenerator[dict, None]:
    """
    Run all agents with SSE progress events.
    Yields dicts with {"event": "...", "data": {...}} for SSE streaming.
    
    Args:
        state: TravelPlannerState containing all planning data
        skip_agents: Optional list of agent names to skip (for re-plan feature)
                     If provided, skipped agents will use existing data from state
    """
    logger.info(f"Agent orchestrator (streaming): selected_cities={state.get('selected_cities', [])}")
    state["agent_errors"] = state.get("agent_errors", [])
    state["progress_updates"] = state.get("progress_updates", [])
    
    # Initialize skip list
    skip_agents = skip_agents or []
    logger.info(f"Skipping agents: {skip_agents}")

    # --- BATCH 1 ---
    batch1_tasks = []
    batch1_keys = []
    batch1_names = []
    
    for agent_name, agent_key, agent_func in [
        ("flight", "flight_data", run_flight_agent),
        ("hotel", "hotel_data", run_hotel_agent),
        ("weather", "weather_data", run_weather_agent),
        ("safety", "safety_data", run_safety_agent),
    ]:
        if agent_name in skip_agents:
            # Skip this agent - use existing data
            yield {"event": "agent_progress", "data": {"agent": agent_name, "status": "skipped", "message": f"{agent_name.title()} unchanged (no impact from your edits)"}}
            logger.info(f"Skipping {agent_name} agent - using existing data")
        else:
            # Run this agent
            yield {"event": "agent_progress", "data": {"agent": agent_name, "status": "working", "message": f"Re-selecting {agent_name}..." if skip_agents else f"Searching for {agent_name}..."}}
            batch1_tasks.append(agent_func(state))
            batch1_keys.append(agent_key)
            batch1_names.append(agent_name)
    
    # Execute batch 1 agents that aren't skipped
    if batch1_tasks:
        results = await asyncio.gather(*batch1_tasks, return_exceptions=True)
    else:
        results = []

    # Process results for batch 1
    for i, (key, name) in enumerate(zip(batch1_keys, batch1_names)):
        if isinstance(results[i], Exception):
            logger.error(f"{name} agent failed: {results[i]}")
            state["agent_errors"].append(f"{name}: {str(results[i])}")
            state[key] = None
            yield {"event": "agent_progress", "data": {"agent": name, "status": "failed", "message": f"{name.title()} research encountered an issue"}}
        else:
            state[key] = results[i]
            yield {"event": "agent_progress", "data": {"agent": name, "status": "complete", "message": f"{name.title()} research complete"}}

    # --- BATCH 2 ---
    batch2_tasks = []
    batch2_keys = []
    batch2_names = []
    
    for agent_name, agent_key, agent_func in [
        ("activity", "activity_data", run_activity_agent),
        ("transport", "transport_data", run_transport_agent),
    ]:
        if agent_name in skip_agents:
            # Skip this agent - use existing data
            yield {"event": "agent_progress", "data": {"agent": agent_name, "status": "skipped", "message": f"{agent_name.title()} unchanged (no impact from your edits)"}}
            logger.info(f"Skipping {agent_name} agent - using existing data")
        else:
            # Run this agent
            yield {"event": "agent_progress", "data": {"agent": agent_name, "status": "working", "message": f"Re-planning {agent_name}..." if skip_agents else f"Planning {agent_name}..."}}
            batch2_tasks.append(agent_func(state))
            batch2_keys.append(agent_key)
            batch2_names.append(agent_name)
    
    # Execute batch 2 agents that aren't skipped
    if batch2_tasks:
        results2 = await asyncio.gather(*batch2_tasks, return_exceptions=True)
    else:
        results2 = []

    # Process results for batch 2
    for i, (key, name) in enumerate(zip(batch2_keys, batch2_names)):
        if isinstance(results2[i], Exception):
            logger.error(f"{name} agent failed: {results2[i]}")
            state["agent_errors"].append(f"{name}: {str(results2[i])}")
            state[key] = None
            yield {"event": "agent_progress", "data": {"agent": name, "status": "failed", "message": f"{name.title()} planning encountered an issue"}}
        else:
            state[key] = results2[i]
            yield {"event": "agent_progress", "data": {"agent": name, "status": "complete", "message": f"{name.title()} planning complete"}}

    # --- BUDGET ---
    # Budget agent almost always runs (unless skipped explicitly)
    if "budget" in skip_agents:
        yield {"event": "agent_progress", "data": {"agent": "budget", "status": "skipped", "message": "Budget unchanged"}}
        logger.info("Skipping budget agent - using existing data")
    else:
        yield {"event": "agent_progress", "data": {"agent": "budget", "status": "working", "message": "Re-calculating budget..." if skip_agents else "Optimizing budget..."}}
        try:
            state["budget_analysis"] = await run_budget_agent(state)
            yield {"event": "agent_progress", "data": {"agent": "budget", "status": "complete", "message": "Budget analysis complete"}}
        except Exception as e:
            logger.error(f"Budget agent failed: {e}")
            state["agent_errors"].append(f"budget: {str(e)}")
            state["budget_analysis"] = None
            yield {"event": "agent_progress", "data": {"agent": "budget", "status": "failed", "message": "Budget analysis encountered an issue"}}

    # --- ASSEMBLY ---
    # Assembler ALWAYS runs to ensure coherence (never skipped)
    yield {"event": "agent_progress", "data": {"agent": "assembler", "status": "working", "message": "Merging your updated itinerary..." if skip_agents else "Assembling your itinerary..."}}
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
