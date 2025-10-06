#!/usr/bin/env python3
"""
GPS Simulator for Autonomous Vehicle Tracking System
Simulates a Raspberry Pi sending GPS data to the backend server
"""

import requests
import time
import json
import random
import math
from datetime import datetime
import argparse
import sys

class GPSSimulator:
    def __init__(self, vehicle_id, server_url, update_interval=5):
        self.vehicle_id = vehicle_id
        self.server_url = server_url
        self.update_interval = update_interval
        self.running = False
        
        # Simulated starting position (New York City)
        self.lat = 40.7128
        self.lon = -74.0060
        self.speed = 0.0
        self.heading = 0.0
        self.battery_level = 100.0
        self.status = "active"
        
        # Movement parameters
        self.max_speed = 50.0  # km/h
        self.speed_change_rate = 0.5
        self.heading_change_rate = 5.0  # degrees per update
        
    def generate_telemetry(self):
        """Generate realistic telemetry data"""
        # Simulate speed changes
        speed_change = random.uniform(-self.speed_change_rate, self.speed_change_rate)
        self.speed = max(0, min(self.max_speed, self.speed + speed_change))
        
        # Simulate heading changes
        heading_change = random.uniform(-self.heading_change_rate, self.heading_change_rate)
        self.heading = (self.heading + heading_change) % 360
        
        # Simulate battery drain
        if self.speed > 0:
            battery_drain = random.uniform(0.1, 0.3)
            self.battery_level = max(0, self.battery_level - battery_drain)
        
        # Simulate GPS movement (rough approximation)
        if self.speed > 0:
            # Convert speed from km/h to degrees per second
            # Rough approximation: 1 degree ≈ 111 km
            speed_deg_per_sec = (self.speed / 111000) * (self.update_interval / 3600)
            
            # Calculate new position based on heading and speed
            lat_change = speed_deg_per_sec * math.cos(math.radians(self.heading))
            lon_change = speed_deg_per_sec * math.sin(math.radians(self.heading))
            
            self.lat += lat_change
            self.lon += lon_change
        
        # Simulate status changes
        if self.battery_level < 10:
            self.status = "low_battery"
        elif self.battery_level <= 0:
            self.status = "inactive"
        else:
            self.status = "active"
    
    def send_location_update(self):
        """Send location update to the server"""
        try:
            data = {
                "vehicle_id": self.vehicle_id,
                "lat": self.lat,
                "lon": self.lon,
                "speed": self.speed,
                "heading": self.heading,
                "battery_level": self.battery_level,
                "status": self.status,
                "timestamp": datetime.utcnow().isoformat(),
                "extras": {
                    "temperature": random.uniform(15, 35),
                    "humidity": random.uniform(30, 80),
                    "signal_strength": random.uniform(70, 100)
                }
            }
            
            response = requests.post(
                f"{self.server_url}/api/update_location",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Vehicle {self.vehicle_id}: "
                      f"Lat={self.lat:.6f}, Lon={self.lon:.6f}, "
                      f"Speed={self.speed:.1f}km/h, "
                      f"Battery={self.battery_level:.1f}%")
            else:
                print(f"Error sending update: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
        except Exception as e:
            print(f"Error: {e}")
    
    def run(self):
        """Main simulation loop"""
        print(f"Starting GPS simulator for Vehicle {self.vehicle_id}")
        print(f"Server URL: {self.server_url}")
        print(f"Update interval: {self.update_interval} seconds")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        self.running = True
        
        try:
            while self.running:
                self.generate_telemetry()
                self.send_location_update()
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            print("\nStopping simulator...")
            self.running = False
        except Exception as e:
            print(f"Simulator error: {e}")
            self.running = False

def main():
    parser = argparse.ArgumentParser(description="GPS Simulator for Vehicle Tracking")
    parser.add_argument("--vehicle-id", default="V001", help="Vehicle ID")
    parser.add_argument("--server-url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--interval", type=int, default=5, help="Update interval in seconds")
    
    args = parser.parse_args()
    
    simulator = GPSSimulator(
        vehicle_id=args.vehicle_id,
        server_url=args.server_url,
        update_interval=args.interval
    )
    
    simulator.run()

if __name__ == "__main__":
    main()