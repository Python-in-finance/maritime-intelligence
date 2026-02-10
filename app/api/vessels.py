"""
Vessel API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func

from app.core.database import get_db
from app.models.vessel import Vessel, VesselPosition

router = APIRouter(prefix="/vessels", tags=["vessels"])


@router.get("")
async def list_vessels(
    bbox: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    vessel_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    List vessels with optional filtering
    """
    # Get latest position for each vessel
    latest_positions_subq = db.query(
        VesselPosition.mmsi,
        func.max(VesselPosition.timestamp).label('latest_time')
    ).group_by(VesselPosition.mmsi).subquery()
    
    query = db.query(VesselPosition).join(
        latest_positions_subq,
        (VesselPosition.mmsi == latest_positions_subq.c.mmsi) &
        (VesselPosition.timestamp == latest_positions_subq.c.latest_time)
    )
    
    # Apply bbox filter
    if bbox:
        try:
            lat_min, lon_min, lat_max, lon_max = map(float, bbox.split(","))
            query = query.filter(
                VesselPosition.latitude >= lat_min,
                VesselPosition.latitude <= lat_max,
                VesselPosition.longitude >= lon_min,
                VesselPosition.longitude <= lon_max
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid bbox format")
    
    total = db.query(VesselPosition.mmsi).distinct().count()
    positions = query.offset(offset).limit(limit).all()
    
    vessels = []
    for pos in positions:
        vessels.append({
            "mmsi": pos.mmsi,
            "vessel_name": pos.vessel_name or f"Vessel {pos.mmsi}",
            "vessel_type": pos.vessel_type or "unknown",
            "imo": None,
            "callsign": None,
            "flag": None,
            "length_overall": None,
            "beam": None,
            "deadweight": None,
            "gross_tonnage": None,
            "build_year": None,
            "positions": [{
                "latitude": pos.latitude,
                "longitude": pos.longitude,
                "timestamp": pos.timestamp.isoformat() if pos.timestamp else None,
                "speed_over_ground": pos.speed_over_ground,
                "course_over_ground": pos.course_over_ground,
                "heading": pos.heading,
                "nav_status": pos.nav_status,
                "destination": pos.destination,
                "eta": pos.eta.isoformat() if pos.eta else None,
                "draught": pos.draught,
                "data_source": pos.data_source
            }]
        })
    
    return {"total": total, "vessels": vessels, "limit": limit, "offset": offset}


@router.get("/{mmsi}")
async def get_vessel(mmsi: int, db: Session = Depends(get_db)):
    """Get vessel by MMSI"""
    position = db.query(VesselPosition).filter(
        VesselPosition.mmsi == mmsi
    ).order_by(VesselPosition.timestamp.desc()).first()
    
    if not position:
        raise HTTPException(status_code=404, detail="Vessel not found")
    
    return {
        "mmsi": position.mmsi,
        "vessel_name": position.vessel_name or f"Vessel {position.mmsi}",
        "vessel_type": position.vessel_type or "unknown",
        "positions": [{
            "latitude": position.latitude,
            "longitude": position.longitude,
            "timestamp": position.timestamp.isoformat() if position.timestamp else None,
            "speed_over_ground": position.speed_over_ground,
            "course_over_ground": position.course_over_ground,
        }] if position else None
    }


@router.get("/{mmsi}/track")
async def get_vessel_track(
    mmsi: int,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get vessel track history"""
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
        "avg_speed": sum(p.speed_over_ground or 0 for p in positions) / len(positions) if positions else 0,
    }
