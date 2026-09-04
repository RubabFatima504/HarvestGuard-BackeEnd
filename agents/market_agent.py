"""
MARKET INTELLIGENCE AGENT
Kaam: Best market dhundho, prices compare karo, scenarios banao
"""
from langchain_core.messages import HumanMessage, SystemMessage
from agents import llm
from rag.pipeline import search_knowledge
from models.scenario_simulator import simulate_scenarios, find_nearest_market, find_premium_market
import json


MARKET_SYSTEM_PROMPT = """You are the Market Intelligence Agent for HarvestGuard.

Your job is to analyze market options for a harvested crop batch and compare selling scenarios.

You will be given:
1. Batch details and current spoilage data
2. Market price data for nearby mandis
3. Three calculated scenarios with financial outcomes
4. Relevant market knowledge from RAG

Provide:
1. Which scenario is best and WHY (be specific about the financial reasoning)
2. Market timing advice (is now a good time to sell, or should they wait?)
3. Any risks the farmer should know about

Be concise, factual, and practical. Write for a cooperative worker, not a scientist.
Keep your response under 200 words."""


async def run_market_agent(batch: dict, spoilage_data: dict) -> dict:
    """
    Market analysis + scenario comparison karo
    Needs spoilage_data from spoilage_agent
    """
    # Step 1: Scenarios calculate karo
    scenarios = simulate_scenarios(
        crop_id=batch["crop_id"],
        quantity_kg=batch["quantity_kg"],
        decay_rate_k=spoilage_data["curve_data"]["decay_rate_k"],
        days_since_harvest=spoilage_data["curve_data"]["days_since_harvest"],
        batch_lat=batch["latitude"],
        batch_lng=batch["longitude"],
        current_value_pct=spoilage_data["curve_data"]["current_value_pct"],
    )

    # Step 2: RAG se market knowledge
    rag_query = f"{batch['crop_id'].replace('_', ' ')} market price Pakistan wholesale mandi best time to sell"
    rag_context = search_knowledge(rag_query, k=3)

    # Step 3: LLM analysis
    scenarios_text = json.dumps(scenarios, indent=2, ensure_ascii=False)
    
    user_message = f"""
Analyze these market scenarios for a batch of {batch['quantity_kg']}kg {batch['crop_id'].replace('_', ' ')}:

SCENARIOS:
{scenarios_text}

MARKET CONTEXT:
{rag_context}

Which scenario do you recommend and why?
"""

    response = await llm.ainvoke([
        SystemMessage(content=MARKET_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    recommended = next((s for s in scenarios if s["is_recommended"]), scenarios[0])

    return {
        "agent": "market_intelligence",
        "status": "completed",
        "scenarios": scenarios,
        "recommended_scenario": recommended["scenario_id"],
        "analysis": response.content,
        "nearest_market": find_nearest_market(batch["latitude"], batch["longitude"]),
    }