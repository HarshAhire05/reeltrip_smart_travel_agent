"""
Budget Agent — sums all costs, converts currency, adds buffer, compares to budget.
If over budget: suggests cuts via gpt-4o-mini.
No external API calls except currency conversion.
"""
import json
import logging

from services.openai_client import call_openai_json
from services.exchange_rate_client import convert, get_exchange_rate

logger = logging.getLogger(__name__)


async def run_budget_agent(state: dict) -> dict:
    """Analyze budget across all agent outputs."""
    prefs = state.get("user_preferences", {})
    selected_cities = state.get("selected_cities", [])

    logger.info(f"[budget] Processing cities: {selected_cities}")
    flight_data = state.get("flight_data")
    hotel_data = state.get("hotel_data")
    activity_data = state.get("activity_data")
    transport_data = state.get("transport_data")

    user_budget = prefs.get("total_budget", 0)
    budget_currency = prefs.get("budget_currency", "INR")
    num_travelers = prefs.get("number_of_travelers", 2)
    duration = prefs.get("trip_duration_days", 3)

    # Get exchange rate from USD to user currency (many estimates are in USD)
    usd_rate = await get_exchange_rate("USD", budget_currency)
    if usd_rate is None:
        usd_rate = 83.0  # Fallback INR rate

    # --- Calculate costs ---
    flights_total = _calc_flight_cost(flight_data, budget_currency, usd_rate, num_travelers)
    accommodation_total = _calc_hotel_cost(hotel_data, budget_currency, usd_rate, duration)
    activities_total = _calc_activity_cost(activity_data, budget_currency, usd_rate, num_travelers)
    food_total = _calc_food_cost(activity_data, budget_currency, usd_rate, num_travelers, duration)
    transport_total = _calc_transport_cost(transport_data, budget_currency, usd_rate, duration)

    subtotal = flights_total + accommodation_total + activities_total + food_total + transport_total
    buffer = round(subtotal * 0.10, 2)  # 10% buffer
    grand_total = round(subtotal + buffer, 2)

    # Determine budget status
    if user_budget <= 0:
        budget_status = "no_budget_set"
    elif grand_total <= user_budget:
        budget_status = "within_budget" if grand_total >= user_budget * 0.7 else "under_budget"
    else:
        budget_status = "over_budget"

    result = {
        "total_estimated_cost": grand_total,
        "currency": budget_currency,
        "user_budget": user_budget,
        "budget_status": budget_status,
        "breakdown": {
            "flights": round(flights_total, 2),
            "accommodation": round(accommodation_total, 2),
            "food": round(food_total, 2),
            "activities": round(activities_total, 2),
            "transportation": round(transport_total, 2),
            "miscellaneous_buffer": round(buffer, 2),
        },
        "exchange_rate_used": usd_rate if budget_currency != "USD" else None,
        "optimization_suggestions": [],
        "potential_savings": 0,
    }

    # If over budget, get optimization suggestions
    if budget_status == "over_budget" and user_budget > 0:
        over_by = grand_total - user_budget
        suggestions = await _get_optimization_suggestions(
            result["breakdown"], user_budget, grand_total, over_by, budget_currency
        )
        result["optimization_suggestions"] = suggestions.get("suggestions", [])
        result["potential_savings"] = suggestions.get("potential_savings", 0)

    return result


def _to_currency(amount: float, from_currency: str, target_currency: str, usd_rate: float) -> float:
    """Convert amount to target currency using USD as intermediary."""
    if from_currency.upper() == target_currency.upper():
        return amount
    if from_currency.upper() == "USD":
        return amount * usd_rate
    # Approximate: assume from_currency is target_currency already or USD
    return amount


def _calc_flight_cost(flight_data: dict | None, currency: str, usd_rate: float, travelers: int) -> float:
    """Sum flight costs."""
    if not flight_data:
        return 0
    total = 0
    # Recommended outbound
    outbound = flight_data.get("recommended_outbound") or (
        flight_data.get("outbound_options", [{}])[0] if flight_data.get("outbound_options") else {}
    )
    price = outbound.get("estimated_price", 0)
    price_curr = outbound.get("price_currency", currency)
    total += _to_currency(price, price_curr, currency, usd_rate) * travelers

    # Recommended return
    ret = flight_data.get("recommended_return") or (
        flight_data.get("return_options", [{}])[0] if flight_data.get("return_options") else {}
    )
    price = ret.get("estimated_price", 0)
    price_curr = ret.get("price_currency", currency)
    total += _to_currency(price, price_curr, currency, usd_rate) * travelers

    # Inter-city flights
    for icf in flight_data.get("inter_city_flights", []):
        price = icf.get("estimated_price", 0)
        price_curr = icf.get("price_currency", currency)
        total += _to_currency(price, price_curr, currency, usd_rate) * travelers

    return total


def _calc_hotel_cost(hotel_data: dict | None, currency: str, usd_rate: float, nights: int) -> float:
    """Sum hotel costs."""
    if not hotel_data:
        return 0
    total = 0
    for hotel in hotel_data.get("recommended_hotels", []):
        ppn = hotel.get("price_per_night_estimate", 0)
        h_curr = hotel.get("currency", currency)
        total += _to_currency(ppn, h_curr, currency, usd_rate) * nights
    return total


def _calc_activity_cost(activity_data: dict | None, currency: str, usd_rate: float, travelers: int) -> float:
    """Sum activity costs."""
    if not activity_data:
        return 0
    total = 0
    for act in activity_data.get("planned_activities", []):
        cost = act.get("estimated_cost_per_person", 0)
        a_curr = act.get("currency", currency)
        total += _to_currency(cost, a_curr, currency, usd_rate) * travelers
    return total


def _calc_food_cost(activity_data: dict | None, currency: str, usd_rate: float, travelers: int, days: int) -> float:
    """Sum restaurant costs."""
    if not activity_data:
        return 0
    total = 0
    restaurants = activity_data.get("restaurant_recommendations", [])
    if restaurants:
        for rest in restaurants:
            cost = rest.get("estimated_cost_per_person", 0)
            r_curr = rest.get("currency", currency)
            total += _to_currency(cost, r_curr, currency, usd_rate) * travelers
    return total


def _calc_transport_cost(transport_data: dict | None, currency: str, usd_rate: float, days: int) -> float:
    """Sum transport costs."""
    if not transport_data:
        return 0
    total = 0

    # Inter-city transport
    for opt in transport_data.get("inter_city_options", []):
        cost = opt.get("estimated_cost", 0)
        t_curr = opt.get("currency", currency)
        total += _to_currency(cost, t_curr, currency, usd_rate)

    # Airport transfers (x2 for arrival and departure)
    for transfer in transport_data.get("airport_transfers", []):
        cost = transfer.get("estimated_cost", 0)
        total += cost * 2  # Assume same cost each way

    # Daily local transport
    for summary in transport_data.get("local_transport_summary", []):
        daily = summary.get("daily_transport_budget", 0)
        total += daily * days

    return total


async def _get_optimization_suggestions(
    breakdown: dict, budget: float, total: float, over_by: float, currency: str
) -> dict:
    """Use gpt-4o-mini to suggest budget cuts."""
    result = await call_openai_json(
        task="fast",
        system_prompt="You are a travel budget optimization assistant. Suggest practical ways to reduce trip costs. Respond in JSON format ONLY.",
        user_prompt=f"""The trip is over budget by {over_by:.0f} {currency}.

Budget: {budget:.0f} {currency}
Estimated total: {total:.0f} {currency}

Cost breakdown:
{json.dumps(breakdown, indent=2)}

Suggest 3-5 specific ways to reduce costs. For each suggestion,
estimate how much it could save.

Return JSON:
{{
    "suggestions": [
        "specific actionable suggestion with estimated savings"
    ],
    "potential_savings": total_potential_savings_number
}}""",
        max_tokens=1024,
        temperature=0.3,
    )

    if result:
        return result
    return {"suggestions": [f"Consider reducing accommodation or activity costs to save {over_by:.0f} {currency}"], "potential_savings": over_by}
