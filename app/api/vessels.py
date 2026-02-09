from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.vessel import Vessel, VesselPosition

router = APIRouter()

@router.get("")
async def list_vessels(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    db = SessionLocal()
    try:
        vessels = db.query(Vessel).offset(offset).limit(limit).all()
        result = []
        for v in vessels:
            position = db.query(VesselPosition).filter(VesselPosition.mmsi == v.mmsi).order_by(VesselPosition.timestamp.desc()).first()
            result.append({
                "mmsi": v.mmsi, "name": v.vessel_name, "type": v.vessel_type,
                "lat": position.latitude if position else None,
                "lon": position.longitude if position else None,
                "speed": position.speed_over_ground if position else None,
                "course": position.course_over_ground if position else None,
                "destination": v.destination, "dwt": v.deadweight, "loa": v.length_overall,
            })
        return {"vessels": result, "total": len(result)}
    finally:
        db.close()

@router.get("/{mmsi}")
async def get_vessel(mmsi: int):
    db = SessionLocal()
    try:
        vessel = db.query(Vessel).filter(Vessel.mmsi == mmsi).first()
        if not vessel:
            raise HTTPException(status_code=404, detail="Vessel not found")
        position = db.query(VesselPosition).filter(VesselPosition.mmsi == mmsi).order_by(VesselPosition.timestamp.desc()).first()
        return {
            "mmsi": vessel.mmsi, "name": vessel.vessel_name, "type": vessel.vessel_type,
            "imo": vessel.imo, "callsign": vessel.callsign, "dwt": vessel.deadweight,
            "loa": vessel.length_overall, "beam": vessel.beam, "destination": vessel.destination,
            "position": {"lat": position.latitude, "lon": position.longitude, "speed": position.speed_over_ground,
                        "course": position.course_over_ground, "timestamp": position.timestamp.isoformat()} if position else None
        }
    finally:
        db.close()

@router.get("/{mmsi}/track")
async def get_vessel_track(mmsi: int, hours: int = Query(24, ge=1, le=168)):
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        positions = db.query(VesselPosition).filter(VesselPosition.mmsi == mmsi, VesselPosition.timestamp >= since).order_by(VesselPosition.timestamp.asc()).all()
        return {
            "mmsi": mmsi,
            "track": [{"lat": p.latitude, "lon": p.longitude, "timestamp": p.timestamp.isoformat(), "speed": p.speed_over_ground} for p in positions],
            "avg_speed": sum(p.speed_over_ground or 0 for p in positions) / len(positions) if positions else 0,
        }
    finally:
        db.close()
