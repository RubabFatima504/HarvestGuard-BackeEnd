"""
LangGraph Orchestrator — Teenon agents ko coordinate karta hai
Flow: Spoilage Agent → Market Agent → Advisory Agent
"""
from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from agents.spoilage_agent import run_spoilage_agent
from agents.market_agent import run_market_agent
from agents.advisory_agent import run_advisory_agent


# State — yeh data har agent ke beech share hota hai
class HarvestState(TypedDict):
    batch: dict                    # User ka input
    spoilage_result: dict | None   # Spoilage agent ka output
    market_result: dict | None     # Market agent ka output
    advisory_result: dict | None   # Advisory agent ka output
    status: str                    # Current status
    error: str | None              # Error agar ho


# ─── Node Functions (har node = ek agent) ───

async def spoilage_node(state: HarvestState) -> HarvestState:
    """Node 1: Spoilage analysis"""
    try:
        result = await run_spoilage_agent(state["batch"])
        return {
            **state,
            "spoilage_result": result,
            "status": "spoilage_complete",
        }
    except Exception as e:
        return {**state, "error": f"Spoilage Agent Error: {str(e)}", "status": "error"}


async def market_node(state: HarvestState) -> HarvestState:
    """Node 2: Market analysis (needs spoilage data)"""
    try:
        result = await run_market_agent(state["batch"], state["spoilage_result"])
        return {
            **state,
            "market_result": result,
            "status": "market_complete",
        }
    except Exception as e:
        return {**state, "error": f"Market Agent Error: {str(e)}", "status": "error"}


async def advisory_node(state: HarvestState) -> HarvestState:
    """Node 3: Advisory report (needs both previous results)"""
    try:
        result = await run_advisory_agent(
            state["batch"],
            state["spoilage_result"],
            state["market_result"],
        )
        return {
            **state,
            "advisory_result": result,
            "status": "complete",
        }
    except Exception as e:
        return {**state, "error": f"Advisory Agent Error: {str(e)}", "status": "error"}


def should_continue(state: HarvestState) -> str:
    """Error hone pe ruko, warna aage jao"""
    if state.get("error"):
        return END
    return "continue"


# ─── Graph Build ───

def build_graph():
    """LangGraph state machine banao"""
    graph = StateGraph(HarvestState)

    # Nodes add karo
    graph.add_node("spoilage_agent", spoilage_node)
    graph.add_node("market_agent", market_node)
    graph.add_node("advisory_agent", advisory_node)

    # Flow define karo: spoilage → market → advisory → END
    graph.set_entry_point("spoilage_agent")
    
    graph.add_conditional_edges("spoilage_agent", should_continue, {
        "continue": "market_agent",
        END: END,
    })
    graph.add_conditional_edges("market_agent", should_continue, {
        "continue": "advisory_agent",
        END: END,
    })
    graph.add_edge("advisory_agent", END)

    return graph.compile()


# Compiled graph — yeh import karke use karo
assessment_graph = build_graph()


async def run_assessment(batch: dict) -> dict:
    """
    MAIN ENTRY POINT — Poora assessment run karo
    batch dict do, poora result milega
    """
    initial_state: HarvestState = {
        "batch": batch,
        "spoilage_result": None,
        "market_result": None,
        "advisory_result": None,
        "status": "started",
        "error": None,
    }

    # Graph invoke karo
    final_state = await assessment_graph.ainvoke(initial_state)

    return {
        "status": final_state["status"],
        "error": final_state.get("error"),
        "spoilage": final_state.get("spoilage_result"),
        "market": final_state.get("market_result"),
        "advisory": final_state.get("advisory_result"),
    }