#!/usr/bin/env python3
"""
Test script for the Autonomous Vehicle Tracker API
"""

import requests
import json
import time
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_location_update():
    """Test location update endpoint"""
    print("🔍 Testing location update...")
    try:
        data = {
            "vehicle_id": "TEST_V001",
            "lat": 40.7128,
            "lon": -74.0060,
            "speed": 25.5,
            "heading": 180.0,
            "battery_level": 85.0,
            "status": "active",
            "timestamp": datetime.utcnow().isoformat(),
            "extras": {
                "temperature": 22.5,
                "humidity": 60.0
            }
        }
        
        response = requests.post(f"{API_BASE_URL}/api/update_location", json=data)
        if response.status_code == 200:
            print("✅ Location update successful")
            return True
        else:
            print(f"❌ Location update failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Location update error: {e}")
        return False

def test_get_latest_locations():
    """Test getting latest locations"""
    print("🔍 Testing get latest locations...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/latest_locations")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved {len(data.get('vehicles', []))} vehicles")
            return True
        else:
            print(f"❌ Get latest locations failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get latest locations error: {e}")
        return False

def test_send_command():
    """Test sending command to vehicle"""
    print("🔍 Testing send command...")
    try:
        data = {
            "vehicle_id": "TEST_V001",
            "command": "test_command",
            "parameters": {"test": "value"}
        }
        
        response = requests.post(f"{API_BASE_URL}/api/send_command", json=data)
        if response.status_code == 200:
            print("✅ Command sent successfully")
            return True
        else:
            print(f"❌ Send command failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Send command error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Starting API tests...")
    print("=" * 50)
    
    tests = [
        test_health,
        test_location_update,
        test_get_latest_locations,
        test_send_command
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())