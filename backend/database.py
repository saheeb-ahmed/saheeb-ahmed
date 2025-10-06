"""
Database models and utilities for the vehicle tracking system
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
import os

# Database connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGODB_URL)
db = client.vehicle_tracker

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class LocationData(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str
    lat: float
    lon: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    battery_level: Optional[float] = None
    status: str = "active"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    extras: Optional[Dict[str, Any]] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class VehicleStatus(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str
    lat: float
    lon: float
    speed: float
    heading: float
    battery_level: float
    status: str
    last_update: datetime = Field(default_factory=datetime.utcnow)
    extras: Optional[Dict[str, Any]] = None

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Command(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    vehicle_id: str
    command: str
    parameters: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Database collections
locations_collection = db.locations
vehicle_status_collection = db.vehicle_status
commands_collection = db.commands

async def create_indexes():
    """Create database indexes for better performance"""
    # Location indexes
    await locations_collection.create_index("vehicle_id")
    await locations_collection.create_index("timestamp")
    await locations_collection.create_index([("vehicle_id", 1), ("timestamp", -1)])
    
    # Vehicle status indexes
    await vehicle_status_collection.create_index("vehicle_id", unique=True)
    
    # Command indexes
    await commands_collection.create_index("vehicle_id")
    await commands_collection.create_index("timestamp")
    await commands_collection.create_index("status")