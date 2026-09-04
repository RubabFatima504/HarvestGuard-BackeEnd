"""HarvestGuard Backend — FastAPI Entry Point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from api.routes import router
from api.auth_routes import router as auth_router
from db import init_db
from rag.pipeline import build_vector_store
from scraper.amis_scraper import run_daily_scrape

# BackgroundScheduler runs jobs in their own separate thread(s), NOT on
# FastAPI's main async event loop. This matters because the scraper uses
# blocking calls (requests.get, time.sleep for Nominatim rate-limiting) -
# if this ran on the main event loop instead, every user request would
# freeze for the scraper's entire runtime. With BackgroundScheduler, the
# API keeps serving requests normally while the scraper runs alongside it.
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App start hone pe DB tables banao + RAG vector store build karo + scraper schedule karo"""
    print("[STARTUP] Initializing database...")
    init_db()

    print("[STARTUP] Building RAG vector store...")
    build_vector_store()
    print("[READY] HarvestGuard backend ready!")

    # Scraper ko roz raat 11 PM (23:00, server ka local time) pe chalao.
    # id diya hai taake agar --reload se ye function dobara chale (dev
    # mode mein hota hai), duplicate job scheduled na ho.
    scheduler.add_job(
        run_daily_scrape,
        trigger="cron",
        hour=23,
        minute=0,
        id="amis_daily_scrape",
        replace_existing=True,
    )
    scheduler.start()
    print("[SCHEDULER] AMIS scraper scheduled for 23:00 daily.")

    yield

    print("[SHUTDOWN] Shutting down...")
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="HarvestGuard API",
    description="AI-powered post-harvest loss prevention for Pakistani farmers",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — frontend se connect karne ke liye
# NOTE: allow_origins=["*"] is fine for local dev, but replace it with your
# real Netlify URL before deploying (see the deployment guide, Phase 4.3).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hackathon ke liye * OK hai
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes register karo
app.include_router(router)
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "HarvestGuard API is running 🌾🛡️", "version": "1.0.0"}


@app.get("/api/health")
async def health():
    """
    Scraper ki 'last run kab hui' status check karne ke liye - taake
    pata chal sake data kitna fresh hai, silently stale na ho jaye.
    """
    next_run = scheduler.get_job("amis_daily_scrape")
    return {
        "status": "ok",
        "scheduler_running": scheduler.running,
        "next_scrape_time": str(next_run.next_run_time) if next_run else None,
    }