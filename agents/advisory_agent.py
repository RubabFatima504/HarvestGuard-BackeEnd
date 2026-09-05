# """
# ADVISORY AGENT
# Kaam: Dono agents ke results combine karke final recommendation + report banao
# """
# from langchain_core.messages import HumanMessage, SystemMessage
# from agents import llm
# from rag.pipeline import search_knowledge
# import json


# ADVISORY_SYSTEM_PROMPT = """You are the Advisory Agent for HarvestGuard — your job is to generate the final Loss Prevention Report.

# You receive analysis from two other AI agents:
# 1. Spoilage Analyst — risk assessment, spoilage curve, risk factors
# 2. Market Intelligence — market comparison, scenarios, financial outcomes

# Your job is to synthesize everything into a clear, actionable report with these sections:

# 1. EXECUTIVE SUMMARY (2-3 sentences — the key finding and urgency)
# 2. RECOMMENDED ACTION (one clear, specific action the farmer/cooperative should take TODAY)
# 3. FINANCIAL IMPACT (how much money is saved by following the recommendation vs doing nothing)
# 4. SUPPORTING EVIDENCE (cite the research data and sources that support this recommendation)
# 5. REGIONAL CONTEXT (how this relates to post-harvest loss in the farmer's region)

# Write in simple, clear English. A cooperative extension worker should be able to read this and act on it within the hour.
# Do NOT use jargon. Do NOT be vague. Be specific with numbers, market names, and timelines.
# Output in valid JSON with keys: executive_summary, recommended_action, financial_impact, supporting_evidence, regional_context"""


# async def run_advisory_agent(
#     batch: dict,
#     spoilage_data: dict,
#     market_data: dict,
# ) -> dict:
#     """
#     Final recommendation + report generate karo
#     Yeh dono agents ka output combine karta hai
#     """
#     # RAG context for regional loss data
#     rag_query = f"Pakistan {batch.get('location_province', 'Sindh')} post harvest loss {batch['crop_id'].replace('_', ' ')} statistics percentage"
#     rag_context = search_knowledge(rag_query, k=3)

#     recommended_scenario = next(
#         (s for s in market_data["scenarios"] if s["is_recommended"]),
#         market_data["scenarios"][0]
#     )
#     worst_scenario = min(market_data["scenarios"], key=lambda s: s["net_revenue"])

#     user_message = f"""
# Generate a Loss Prevention Report for this batch:

# BATCH:
# - Crop: {batch['crop_id'].replace('_', ' ')}
# - Quantity: {batch['quantity_kg']} kg
# - Location: {batch.get('location_district', 'Unknown')}, {batch.get('location_province', 'Sindh')}
# - Harvest Date: {batch['harvest_date']}
# - Farmer: {batch.get('farmer_name', 'Not specified')}

# SPOILAGE ANALYSIS:
# - Risk Level: {spoilage_data['risk_level']} ({spoilage_data['risk_score']}/100)
# - Current Value: {spoilage_data['curve_data']['current_value_pct']}%
# - Critical Loss Day: Day {spoilage_data['curve_data']['critical_day']}
# - Temperature: {spoilage_data['current_temp']}°C (ideal: {spoilage_data['curve_data']['ideal_temp']}°C)

# BEST SCENARIO: {recommended_scenario['title']}
# - Market: {recommended_scenario['market_name']}
# - Net Revenue: ₨{recommended_scenario['net_revenue']:,}
# - Spoilage Risk: {recommended_scenario['spoilage_risk_pct']}%

# WORST SCENARIO: {worst_scenario['title']}
# - Net Revenue: ₨{worst_scenario['net_revenue']:,}

# SAVINGS: ₨{recommended_scenario['net_revenue'] - worst_scenario['net_revenue']:,}

# REGIONAL DATA:
# {rag_context}

# Generate the report in JSON format.
# """

#     response = await llm.ainvoke([
#         SystemMessage(content=ADVISORY_SYSTEM_PROMPT),
#         HumanMessage(content=user_message),
#     ])

#     # Try to parse JSON response
#     try:
#         # Clean the response (remove markdown code blocks if present)
#         content = response.content.strip()
#         if content.startswith("```"):
#             content = content.split("\n", 1)[1]  # Remove first line
#             content = content.rsplit("```", 1)[0]  # Remove last ```
#         report = json.loads(content)
#     except json.JSONDecodeError:
#         report = {
#             "executive_summary": response.content,
#             "recommended_action": recommended_scenario["description"],
#             "financial_impact": f"Following this recommendation saves ₨{recommended_scenario['net_revenue'] - worst_scenario['net_revenue']:,}",
#             "supporting_evidence": "Based on FAO post-harvest loss data and crop shelf-life research",
#             "regional_context": "Post-harvest losses in this region average 35-40% for this crop",
#         }

#     return {
#         "agent": "advisory",
#         "status": "completed",
#         "report": report,
#         "recommended_action": recommended_scenario["description"],
#         "savings_pkr": recommended_scenario["net_revenue"] - worst_scenario["net_revenue"],
#     }



"""
ADVISORY AGENT
Kaam: Dono agents ke results combine karke final recommendation + report banao
"""
from langchain_core.messages import HumanMessage, SystemMessage
from agents import llm
from rag.pipeline import search_knowledge
import json
import re


ADVISORY_SYSTEM_PROMPT = """You are the Advisory Agent for HarvestGuard — your job is to generate the final Loss Prevention Report.

You receive analysis from two other AI agents:
1. Spoilage Analyst — risk assessment, spoilage curve, risk factors
2. Market Intelligence — market comparison, scenarios, financial outcomes

Your job is to synthesize everything into a clear, actionable report with these sections:

1. EXECUTIVE SUMMARY (2-3 sentences — the key finding and urgency)
2. RECOMMENDED ACTION (one clear, specific action the farmer/cooperative should take TODAY)
3. FINANCIAL IMPACT (how much money is saved by following the recommendation vs doing nothing)
4. SUPPORTING EVIDENCE (cite the research data and sources that support this recommendation)
5. REGIONAL CONTEXT (how this relates to post-harvest loss in the farmer's region)

Write in simple, clear English. A cooperative extension worker should be able to read this and act on it within the hour.
Do NOT use jargon. Do NOT be vague. Be specific with numbers, market names, and timelines.
Output in valid JSON with keys: executive_summary, recommended_action, financial_impact, supporting_evidence, regional_context.
Every value MUST be a single plain string — never a list, never a nested object."""


# ─── Naye helper functions: LLM ke output ko safe/predictable banane ke liye ───

def _normalize_field(value) -> str:
    """LLM system prompt mein bola gaya hai ke sirf string do, phir bhi
    kabhi list ya dict bana deta hai (e.g. supporting_evidence: [..]).
    Frontend .split() call karta hai jo sirf string pe kaam karta hai —
    list/dict pass hone se 'e.split is not a function' crash hota hai.
    Yahan hum guarantee karte hain ke return value hamesha plain string ho."""
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{k}: {v}" for k, v in value.items())
    if value is None:
        return ""
    return str(value)


def _extract_numbers(text: str) -> list:
    """Text mein se saare numbers nikalo (commas hata ke) — LLM ke likhe
    rupya figure ko humare khud calculate kiye hue number se compare
    karne ke liye."""
    numbers = []
    for match in re.findall(r"[\d,]+(?:\.\d+)?", text):
        try:
            numbers.append(float(match.replace(",", "")))
        except ValueError:
            continue
    return numbers


def _verify_financial_claim(financial_impact_text: str, expected_savings: float, tolerance: float = 0.05) -> bool:
    """Check karo LLM ne jo rupya figure likha hai wo humare khud
    calculate kiye hue savings se (5% tolerance ke sath) match karta hai.
    Match na ho to LLM ki likhi financial_impact pe bharosa mat karo —
    ye hi asli 'wrong decision' wala khatra hai jo humne discuss kiya tha."""
    if expected_savings <= 0:
        return True
    return any(
        abs(n - expected_savings) <= expected_savings * tolerance
        for n in _extract_numbers(financial_impact_text)
    )


async def run_advisory_agent(
    batch: dict,
    spoilage_data: dict,
    market_data: dict,
) -> dict:
    """
    Final recommendation + report generate karo
    Yeh dono agents ka output combine karta hai
    """
    rag_query = f"Pakistan {batch.get('location_province', 'Sindh')} post harvest loss {batch['crop_id'].replace('_', ' ')} statistics percentage"
    rag_context = search_knowledge(rag_query, k=3)

    recommended_scenario = next(
        (s for s in market_data["scenarios"] if s["is_recommended"]),
        market_data["scenarios"][0]
    )
    worst_scenario = min(market_data["scenarios"], key=lambda s: s["net_revenue"])
    expected_savings = recommended_scenario["net_revenue"] - worst_scenario["net_revenue"]

    user_message = f"""
Generate a Loss Prevention Report for this batch:

BATCH:
- Crop: {batch['crop_id'].replace('_', ' ')}
- Quantity: {batch['quantity_kg']} kg
- Location: {batch.get('location_district', 'Unknown')}, {batch.get('location_province', 'Sindh')}
- Harvest Date: {batch['harvest_date']}
- Farmer: {batch.get('farmer_name', 'Not specified')}

SPOILAGE ANALYSIS:
- Risk Level: {spoilage_data['risk_level']} ({spoilage_data['risk_score']}/100)
- Current Value: {spoilage_data['curve_data']['current_value_pct']}%
- Critical Loss Day: Day {spoilage_data['curve_data']['critical_day']}
- Temperature: {spoilage_data['current_temp']}°C (ideal: {spoilage_data['curve_data']['ideal_temp']}°C)

BEST SCENARIO: {recommended_scenario['title']}
- Market: {recommended_scenario['market_name']}
- Net Revenue: ₨{recommended_scenario['net_revenue']:,}
- Spoilage Risk: {recommended_scenario['spoilage_risk_pct']}%

WORST SCENARIO: {worst_scenario['title']}
- Net Revenue: ₨{worst_scenario['net_revenue']:,}

SAVINGS: ₨{expected_savings:,}

REGIONAL DATA:
{rag_context}

Generate the report in JSON format.
"""

    response = await llm.ainvoke([
        SystemMessage(content=ADVISORY_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    fallback_report = {
        "executive_summary": response.content,
        "recommended_action": recommended_scenario["description"],
        "financial_impact": f"Following this recommendation saves ₨{expected_savings:,}",
        "supporting_evidence": "Based on FAO post-harvest loss data and crop shelf-life research",
        "regional_context": "Post-harvest losses in this region average 35-40% for this crop",
    }

    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        report = json.loads(content)

        # Type-safety: har field ko plain string mein normalize karo,
        # taake frontend ka .split() kabhi crash na ho
        required_keys = ["executive_summary", "recommended_action",
                          "financial_impact", "supporting_evidence", "regional_context"]
        report = {key: _normalize_field(report.get(key)) for key in required_keys}

        # Sanity check: agar koi field khali reh gaya, fallback use karo
        for key in required_keys:
            if not report[key].strip():
                report[key] = fallback_report[key]

        # Financial accuracy check: LLM ne jo rupya figure likha hai wo
        # humare khud calculate kiye hue savings se match karta hai ya nahi
        if not _verify_financial_claim(report["financial_impact"], expected_savings):
            print(f"[ADVISORY] financial_impact mismatch — LLM said something "
                  f"inconsistent with expected ₨{expected_savings:,}, using fallback")
            report["financial_impact"] = fallback_report["financial_impact"]

    except (json.JSONDecodeError, IndexError):
        report = fallback_report

    return {
        "agent": "advisory",
        "status": "completed",
        "report": report,
        "recommended_action": recommended_scenario["description"],
        "savings_pkr": expected_savings,
    }