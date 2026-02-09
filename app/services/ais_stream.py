import asyncio
import json
import logging
import websockets
from datetime import datetime
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.vessel import VesselPosition, Vessel

logger = logging.getLogger(__name__)

class AISStreamClient:
    WEBSOCKET_URL = "wss://stream.aisstream.io/v0/stream"
    
    def __init__(self):
        self.api_key = settings.AISSTREAM_API_KEY
        self.websocket = None
        self.running = False
        self.messages_received = 0
        self.positions_processed = 0
        
    async def connect(self):
        if not self.api_key:
            logger.error("AISStream API key not configured")
            return False
        try:
            logger.info("Connecting to aisstream.io...")
            self.websocket = await websockets.connect(self.WEBSOCKET_URL)
            subscription = {"APIKey": self.api_key, "BoundingBoxes": [[[-90, -180], [90, 180]]]}
            await self.websocket.send(json.dumps(subscription))
            logger.info("Subscription sent")
            self.running = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
            
    async def receive_messages(self):
        while self.running and self.websocket:
            try:
                message = await self.websocket.recv()
                self.messages_received += 1
                data = json.loads(message)
                await self._process_message(data)
            except Exception as e:
                logger.error(f"Error: {e}")
                break
                
    async def _process_message(self, data):
        if "error" in data:
            logger.error(f"AIS error: {data['error']}")
            return
        if data.get("MessageType") == "PositionReport":
            await self._process_position_report(data)
            
    async def _process_position_report(self, data):
        try:
            metadata = data.get("MetaData", {})
            message = data.get("Message", {}).get("PositionReport", {})
            mmsi = metadata.get("MMSI")
            if not mmsi:
                return
            db = SessionLocal()
            try:
                position = VesselPosition(
                    mmsi=int(mmsi),
                    latitude=message.get("Latitude"),
                    longitude=message.get("Longitude"),
                    timestamp=datetime.utcnow(),
                    speed_over_ground=message.get("Sog"),
                    course_over_ground=message.get("Cog"),
                    heading=message.get("TrueHeading"),
                    nav_status=message.get("NavigationalStatus"),
                    data_source="aisstream"
                )
                db.add(position)
                vessel = db.query(Vessel).filter(Vessel.mmsi == int(mmsi)).first()
                if not vessel:
                    vessel = Vessel(mmsi=int(mmsi), vessel_name=metadata.get("ShipName", "").strip())
                    db.add(vessel)
                db.commit()
                self.positions_processed += 1
                if self.positions_processed % 100 == 0:
                    logger.info(f"Processed {self.positions_processed} positions")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error processing position: {e}")
            
    async def run(self):
        while True:
            if await self.connect():
                await self.receive_messages()
            if not self.running:
                break
            logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
            
    def get_stats(self):
        return {
            "messages_received": self.messages_received,
            "positions_processed": self.positions_processed,
            "connected": self.websocket is not None,
            "running": self.running,
        }

ais_stream_client = AISStreamClient()

async def start_ais_stream():
    if settings.AISSTREAM_API_KEY:
        logger.info("Starting AIS stream...")
        await ais_stream_client.run()
    else:
        logger.warning("AISSTREAM_API_KEY not set")
        
async def stop_ais_stream():
    await ais_stream_client.disconnect()
