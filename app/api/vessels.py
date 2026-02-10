"""
Vessel API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models.vessel import VesselPosition

router = APIRouter()


@router.get("")
async def list_vessels(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    """List vessels with latest positions"""
    try:
        db = SessionLocal()
        positions = db.query(VesselPosition).order_by(VesselPosition.timestamp.desc()).limit(limit).offset(offset).all()
        
        seen_mmsi = set()
        vessels = []
        for pos in positions:
            if pos.mmsi not in seen_mmsi:
                seen_mmsi.add(pos.mmsi)
                vessels.append({
                    "mmsi": pos.mmsi,
                    "name": pos.vessel_name or f"Vessel {pos.mmsi}",
                    "type": pos.vessel_type or "unknown",
                    "lat": pos.latitude,
                    "lon": pos.longitude,
                    "speed": pos.speed_over_ground,
                    "course": pos.course_over_ground,
                    "destination": pos.destination,
                })
        
        total = db.query(VesselPosition.mmsi).distinct().count()
        return {"total": total, "vessels": vessels, "limit": limit, "offset": offset}
    except Exception as e:
        return {"error": str(e), "total": 0, "vessels": [], "limit": limit, "offset": offset}


@router.get("/{mmsi}")
async def get_vessel(mmsi: int):
    """Get vessel by MMSI"""
    db = SessionLocal()
    pos = db.query(VesselPosition).filter(VesselPosition.mmsi == mmsi).order_by(VesselPosition.timestamp.desc()).first()
    if not pos:
        raise HTTPException(status_code=404, detail="Vessel not found")
    return {
        "mmsi": pos.mmsi, "name": pos.vessel_name or f"Vessel {pos.mmsi}",
        "type": pos.vessel_type or "unknown",
        "lat": pos.latitude, "lon": pos.longitude,
        "speed": pos.speed_over_ground, "course": pos.course_over_ground,
    }


@router.get("/{mmsi}/track")
async def get_vessel_track(mmsi: int, hours: int = Query(24, ge=1, le=168)):
    """Get vessel track history"""
    db = SessionLocal()
    since = datetime.utcnow() - timedelta(hours=hours)
    positions = db.query(VesselPosition).filter(VesselPosition.mmsi == mmsi, VesselPosition.timestamp >= since).order_by(VesselPosition.timestamp.asc()).all()
    return {
        "mmsi": mmsi,
        "track": [{"lat": p.latitude, "lon": p.longitude, "timestamp": p.timestamp.isoformat() if p.timestamp else None, "speed": p.speed_over_ground} for p in positions],
    }
