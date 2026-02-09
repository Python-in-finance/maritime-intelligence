from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base

class Vessel(Base):
    __tablename__ = "vessels"
    mmsi = Column(Integer, primary_key=True)
    imo = Column(Integer, nullable=True)
    vessel_name = Column(String(255), nullable=True)
    vessel_type = Column(String(50), nullable=True)
    callsign = Column(String(20), nullable=True)
    length_overall = Column(Float, nullable=True)
    beam = Column(Float, nullable=True)
    deadweight = Column(Integer, nullable=True)
    destination = Column(String(255), nullable=True)

class VesselPosition(Base):
    __tablename__ = "vessel_positions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    mmsi = Column(Integer, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    speed_over_ground = Column(Float, nullable=True)
    course_over_ground = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    nav_status = Column(Integer, nullable=True)
    data_source = Column(String(50), default="aisstream")
