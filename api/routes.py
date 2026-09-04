"""API Endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from api.models import BatchCreate
from agents.orchestrator import run_assessment
from db import Batch, User, get_session
from auth import get_current_user
import uuid
import json

router = APIRouter()


def _batch_to_dict(batch: Batch) -> dict:
    """Same shape the old in-memory `batches[batch_id]` dict used to have,
    so run_assessment() and the frontend's expected response shape don't
    need to change."""
    return {
        "batch_id": batch.batch_id,
        "crop_id": batch.crop_id,
        "quantity_kg": batch.quantity_kg,
        "harvest_date": batch.harvest_date,
        "location_district": batch.location_district,
        "location_province": batch.location_province,
        "latitude": batch.latitude,
        "longitude": batch.longitude,
        "storage_type": batch.storage_type,
        "current_temp_celsius": batch.current_temp_celsius,
        "transport_available": batch.transport_available,
        "hours_to_nearest_market": batch.hours_to_nearest_market,
        "target_market_id": batch.target_market_id,
        "farmer_name": batch.farmer_name,
        "cooperative_name": batch.cooperative_name,
    }


@router.post("/api/batch")
async def create_batch(
    batch: BatchCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Naya batch register karo — current logged-in user ke naam se"""
    batch_id = f"MNG-{uuid.uuid4().hex[:6].upper()}"
    db_batch = Batch(batch_id=batch_id, user_id=current_user.id, **batch.model_dump())
    session.add(db_batch)
    session.commit()
    return {"batch_id": batch_id, "status": "created", "message": "Batch registered successfully"}


@router.get("/api/batch/{batch_id}")
async def get_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Batch details do (sirf apne batches ke)"""
    db_batch = session.get(Batch, batch_id)
    if not db_batch or db_batch.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _batch_to_dict(db_batch)


@router.get("/api/batches")
async def list_batches(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Sirf current user ke batches list karo"""
    db_batches = session.exec(select(Batch).where(Batch.user_id == current_user.id)).all()
    return [_batch_to_dict(b) for b in db_batches]


@router.post("/api/batch/{batch_id}/assess")
async def assess_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """AI Assessment run karo — yeh MAIN endpoint hai"""
    db_batch = session.get(Batch, batch_id)
    if not db_batch or db_batch.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Run the full multi-agent assessment
    result = await run_assessment(_batch_to_dict(db_batch))

    db_batch.set_assessment(result)
    session.add(db_batch)
    session.commit()

    return result


@router.get("/api/batch/{batch_id}/assessment")
async def get_assessment(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Assessment results do (agar pehle run ho chuka ho)"""
    db_batch = session.get(Batch, batch_id)
    if not db_batch or db_batch.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Batch not found")

    result = db_batch.assessment()
    if result is None:
        raise HTTPException(status_code=404, detail="Assessment not found. Run POST /assess first.")
    return result


@router.get("/api/batch/{batch_id}/scenarios")
async def get_scenarios(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Sirf scenarios do"""
    db_batch = session.get(Batch, batch_id)
    if not db_batch or db_batch.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Batch not found")

    result = db_batch.assessment()
    if result is None:
        raise HTTPException(status_code=404, detail="Run assessment first")
    return result.get("market", {}).get("scenarios", [])


@router.get("/api/batch/{batch_id}/report")
async def get_report(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Loss Prevention Report do"""
    db_batch = session.get(Batch, batch_id)
    if not db_batch or db_batch.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Batch not found")

    result = db_batch.assessment()
    if result is None:
        raise HTTPException(status_code=404, detail="Run assessment first")
    return result.get("advisory", {}).get("report", {})


@router.get("/api/markets")
async def list_markets():
    """Available markets list karo"""
    from pathlib import Path
    markets_path = Path(__file__).parent.parent / "data" / "markets.json"
    with open(markets_path, "r") as f:
        return json.load(f)
