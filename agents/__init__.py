"""LLM setup — Groq FREE API (OpenAI-compatible)"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

# Groq FREE API — llama-3.3-70b-versatile
# OpenAI-compatible hai, sirf base_url aur key change karna hota hai
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "qwen/qwen3.8-27b"),
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
    temperature=0.3,
)

# Same model for lite tasks (Groq is already very fast)
llm_lite = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "qwen/qwen3.8-27b"),
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1"),
    temperature=0.2,
)