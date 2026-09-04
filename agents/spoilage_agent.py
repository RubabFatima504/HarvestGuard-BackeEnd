"""
SPOILAGE ANALYST AGENT
Kaam: Batch ka spoilage risk assess karo
Input: batch data (crop, temp, storage, harvest date)
Output: spoilage curve + risk score + risk factors
"""
from langchain_core.messages import HumanMessage, SystemMessage
from agents import llm
from rag.pipeline import search_knowledge
from models.spoilage_curve import generate_spoilage_curve
from utils.weather import get_current_weather
import json


SPOILAGE_SYSTEM_PROMPT = """You are the Spoilage Analyst Agent for HarvestGuard, an AI system that prevents post-harvest crop losses in Pakistan.

Your job is to analyze a harvested crop batch and assess its spoilage risk.

You will be given:
1. Batch details (crop type, harvest date, storage type, quantity)
2. Current weather data (temperature, humidity)
3. Spoilage curve data (calculated from published shelf-life research)
4. Relevant knowledge from agricultural research papers (RAG context)

Based on ALL of this information, provide:
1. A clear risk assessment (HIGH/MEDIUM/LOW)
2. The key risk factors and why they matter
3. How many days until critical quality loss
4. Specific observations about this batch's situation

Be factual. Cite the research context provided. Write in clear, simple English that a cooperative worker can understand.
Keep your response under 250 words."""


async def run_spoilage_agent(batch: dict) -> dict:
    """
    Main function — Spoilage analysis karo
    
    batch = {
        "crop_id": "mango_sindhri",
        "harvest_date": "2026-08-20",
        "storage_type": "open_air",
        "latitude": 25.5276,
        "longitude": 69.0159,
        "quantity_kg": 1000,
        "current_temp_celsius": None  (optional, auto-fill hoga)
    }
    """
    # Step 1: Weather data laao
    weather = get_current_weather(batch["latitude"], batch["longitude"])
    current_temp = batch.get("current_temp_celsius") or weather["temperature"]

    # Step 2: Spoilage curve calculate karo
    curve_data = generate_spoilage_curve(
        crop_id=batch["crop_id"],
        harvest_date=batch["harvest_date"],
        current_temp=current_temp,
        storage_type=batch.get("storage_type", "open_air"),
    )

    # Step 3: RAG se relevant knowledge dhundho
    rag_query = f"{batch['crop_id'].replace('_', ' ')} shelf life at {current_temp}°C storage {batch.get('storage_type', 'open air')} post harvest loss"
    rag_context = search_knowledge(rag_query, k=5)

    # Step 4: LLM ko sab kuch bhejke analysis karwao
    user_message = f"""
Analyze this harvested crop batch for spoilage risk:

BATCH DETAILS:
- Crop: {curve_data['crop_name']}
- Quantity: {batch['quantity_kg']} kg
- Harvest Date: {batch['harvest_date']}
- Days Since Harvest: {curve_data['days_since_harvest']}
- Storage Type: {batch.get('storage_type', 'open_air')}

WEATHER DATA:
- Current Temperature: {current_temp}°C
- Ideal Storage Temperature: {curve_data['ideal_temp']}°C
- Humidity: {weather['humidity']}%

SPOILAGE MODEL RESULTS:
- Current Value Retention: {curve_data['current_value_pct']}%
- Decay Rate (k): {curve_data['decay_rate_k']}
- Critical Day (value drops below 60%): Day {curve_data['critical_day']}
- Risk Score: {curve_data['risk_score']}/100
- Risk Level: {curve_data['risk_level']}

RESEARCH CONTEXT (from agricultural publications):
{rag_context}

Provide your spoilage risk analysis.
"""

    response = await llm.ainvoke([
        SystemMessage(content=SPOILAGE_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    return {
        "agent": "spoilage_analyst",
        "status": "completed",
        "weather": weather,
        "current_temp": current_temp,
        "curve_data": curve_data,
        "risk_score": curve_data["risk_score"],
        "risk_level": curve_data["risk_level"],
        "analysis": response.content,
        "risk_factors": {
            "temperature": {
                "current": current_temp,
                "ideal": curve_data["ideal_temp"],
                "risk_pct": min(100, max(0, int((current_temp - curve_data["ideal_temp"]) * 4))),
            },
            "time_since_harvest": {
                "days": curve_data["days_since_harvest"],
                "risk_pct": min(100, curve_data["days_since_harvest"] * 20),
            },
            "storage_quality": {
                "type": batch.get("storage_type", "open_air"),
                "risk_pct": {"open_air": 90, "covered_shed": 40, "cold_storage": 10}.get(
                    batch.get("storage_type", "open_air"), 70
                ),
            },
            "transport_delay": {
                "hours": batch.get("hours_to_nearest_market", 3),
                "risk_pct": min(100, int(batch.get("hours_to_nearest_market", 3) * 10)),
            },
        },
    }