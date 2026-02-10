"""
Vessel API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models.vessel import VesselPosition

router = APIRouter()


@router.get("")
async def list_vessels(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    List vessels with latest positions
    """
    try:
        db = SessionLocal()
        
        # Simple query - get all positions ordered by timestamp
        positions = db.query(VesselPosition).order_by(
            VesselPosition.timestamp.desc()
        ).limit(limit).offset(offset).all()
        
        # Group by MMSI to get unique vessels
        seen_mmsi = set()
        vessels = []
        
        for pos in positions:
            if pos.mmsi not in seen_mmsi:
                seen_mmsi.add(pos.mmsi)
                vessels.append({
                    "mmsi": pos.mmsi,
                    "vessel_name": pos.vessel_name or f"Vessel {pos.mmsi}",
                    "vessel_type": pos.vessel_type or "unknown",
                    "lat": pos.latitude,
                    "lon": pos.longitude,
                    "speed": pos.speed_over_ground,
                    "course": pos.course_over_ground,
                    "timestamp": pos.timestamp.isoformat() if pos.timestamp else None,
                    "destination": pos.destination,
                })
        
        # Get total unique vessels count
        total = db.query(VesselPosition.mmsi).distinct().count()
        
        return {"total": total, "vessels": vessels, "limit": limit, "offset": offset}
        
    except Exception as e:
        return {"error": str(e), "total": 0, "vessels": [], "limit": limit, "offset": offset}


@router.get("/{mmsi}")
async def get_vessel(mmsi: int):
    """Get vessel by MMSI"""
    try:
        db = SessionLocal()
        position = db.query(VesselPosition).filter(
            VesselPosition.mmsi == mmsi
        ).order_by(VesselPosition.timestamp.desc()).first()
        
        if not position:
            raise HTTPException(status_code=404, detail="Vessel not found")
        
        return {
            "mmsi": position.mmsi,
            "vessel_name": position.vessel_name or f"Vessel {position.mmsi}",
            "lat": position.latitude,
            "lon": position.longitude,
            "speed": position.speed_over_ground,
            "course": position.course_over_ground,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{mmsi}/track")
async def get_vessel_track(mmsi: int, hours: int = Query(24, ge=1, le=168)):
    """Get vessel track history"""
    try:
        db = SessionLocal()
        since = datetime.utcnow() - timedelta(hours=hours)
        
        positions = db.query(VesselPosition).filter(
            VesselPosition.mmsi == mmsi,
            VesselPosition.timestamp >= since
        ).order_by(VesselPosition.timestamp.asc()).all()
        
        return {
            "mmsi": mmsi,
            "track": [{
                "lat": p.latitude,
                "lon": p.longitude,
                "timestamp": p.timestamp.isoformat() if p.timestamp else None,
                "speed": p.speed_over_ground,
            } for p in positions],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
