from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Autonomous Vehicle Tracker API",
    description="Real-time tracking system for autonomous vehicles",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.vehicle_tracker

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class LocationUpdate(BaseModel):
    vehicle_id: str
    lat: float
    lon: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    battery_level: Optional[float] = None
    status: Optional[str] = "active"
    timestamp: Optional[datetime] = None
    extras: Optional[Dict[str, Any]] = None

class VehicleStatus(BaseModel):
    vehicle_id: str
    lat: float
    lon: float
    speed: float
    heading: float
    battery_level: float
    status: str
    last_update: datetime
    extras: Optional[Dict[str, Any]] = None

class Command(BaseModel):
    vehicle_id: str
    command: str
    parameters: Optional[Dict[str, Any]] = None

# API Routes
@app.get("/")
async def root():
    return {"message": "Autonomous Vehicle Tracker API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/update_location")
async def update_location(location: LocationUpdate):
    """Update vehicle location and telemetry data"""
    try:
        # Set timestamp if not provided
        if not location.timestamp:
            location.timestamp = datetime.utcnow()
        
        # Store in database
        location_data = location.dict()
        location_data["_id"] = ObjectId()
        
        await db.locations.insert_one(location_data)
        
        # Update latest vehicle status
        await db.vehicle_status.update_one(
            {"vehicle_id": location.vehicle_id},
            {
                "$set": {
                    "vehicle_id": location.vehicle_id,
                    "lat": location.lat,
                    "lon": location.lon,
                    "speed": location.speed or 0,
                    "heading": location.heading or 0,
                    "battery_level": location.battery_level or 100,
                    "status": location.status,
                    "last_update": location.timestamp,
                    "extras": location.extras or {}
                }
            },
            upsert=True
        )
        
        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "location_update",
            "data": location_data
        })
        
        logger.info(f"Updated location for vehicle {location.vehicle_id}")
        return {"status": "success", "message": "Location updated"}
        
    except Exception as e:
        logger.error(f"Error updating location: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update location")

@app.get("/api/latest_location/{vehicle_id}")
async def get_latest_location(vehicle_id: str):
    """Get latest location for a specific vehicle"""
    try:
        vehicle_status = await db.vehicle_status.find_one({"vehicle_id": vehicle_id})
        if not vehicle_status:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Convert ObjectId to string for JSON serialization
        vehicle_status["_id"] = str(vehicle_status["_id"])
        return vehicle_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest location: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get latest location")

@app.get("/api/latest_locations")
async def get_all_latest_locations():
    """Get latest locations for all vehicles"""
    try:
        vehicles = []
        async for vehicle in db.vehicle_status.find():
            vehicle["_id"] = str(vehicle["_id"])
            vehicles.append(vehicle)
        
        return {"vehicles": vehicles}
        
    except Exception as e:
        logger.error(f"Error getting latest locations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get latest locations")

@app.get("/api/history/{vehicle_id}")
async def get_location_history(
    vehicle_id: str,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None,
    limit: int = 100
):
    """Get location history for a vehicle"""
    try:
        query = {"vehicle_id": vehicle_id}
        
        if from_time or to_time:
            query["timestamp"] = {}
            if from_time:
                query["timestamp"]["$gte"] = from_time
            if to_time:
                query["timestamp"]["$lte"] = to_time
        
        locations = []
        async for location in db.locations.find(query).sort("timestamp", -1).limit(limit):
            location["_id"] = str(location["_id"])
            locations.append(location)
        
        return {"vehicle_id": vehicle_id, "locations": locations}
        
    except Exception as e:
        logger.error(f"Error getting location history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get location history")

@app.post("/api/send_command")
async def send_command(command: Command):
    """Send command to vehicle"""
    try:
        # Store command in database
        command_data = command.dict()
        command_data["timestamp"] = datetime.utcnow()
        command_data["status"] = "pending"
        command_data["_id"] = ObjectId()
        
        await db.commands.insert_one(command_data)
        
        # Broadcast to WebSocket clients
        await manager.broadcast({
            "type": "command",
            "data": command_data
        })
        
        logger.info(f"Command sent to vehicle {command.vehicle_id}: {command.command}")
        return {"status": "success", "message": "Command sent"}
        
    except Exception as e:
        logger.error(f"Error sending command: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send command")

@app.get("/api/vehicles")
async def get_vehicles():
    """Get list of all tracked vehicles"""
    try:
        vehicles = []
        async for vehicle in db.vehicle_status.find():
            vehicle["_id"] = str(vehicle["_id"])
            vehicles.append(vehicle)
        
        return {"vehicles": vehicles}
        
    except Exception as e:
        logger.error(f"Error getting vehicles: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get vehicles")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)