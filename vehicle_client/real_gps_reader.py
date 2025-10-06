#!/usr/bin/env python3
"""
Real GPS Reader for Raspberry Pi
Reads GPS data from serial port and sends to backend server
"""

import serial
import requests
import time
import json
import re
from datetime import datetime
import argparse
import sys

class GPSReader:
    def __init__(self, vehicle_id, server_url, serial_port="/dev/ttyUSB0", baud_rate=9600):
        self.vehicle_id = vehicle_id
        self.server_url = server_url
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.serial_connection = None
        self.running = False
        
        # GPS data
        self.lat = None
        self.lon = None
        self.speed = 0.0
        self.heading = 0.0
        self.battery_level = 100.0  # Would be read from actual battery sensor
        self.status = "active"
        
    def connect_serial(self):
        """Connect to GPS serial port"""
        try:
            self.serial_connection = serial.Serial(
                self.serial_port,
                self.baud_rate,
                timeout=1
            )
            print(f"Connected to GPS on {self.serial_port}")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to GPS: {e}")
            return False
    
    def parse_nmea_sentence(self, sentence):
        """Parse NMEA GPS sentence"""
        if not sentence.startswith('$'):
            return None
            
        parts = sentence.strip().split(',')
        
        if parts[0] == '$GPRMC':
            # Recommended Minimum Specific GPS/Transit Data
            if len(parts) >= 12 and parts[2] == 'A':  # Valid fix
                try:
                    # Latitude
                    lat_deg = float(parts[3][:2])
                    lat_min = float(parts[3][2:])
                    lat = lat_deg + (lat_min / 60.0)
                    if parts[4] == 'S':
                        lat = -lat
                    
                    # Longitude
                    lon_deg = float(parts[5][:3])
                    lon_min = float(parts[5][3:])
                    lon = lon_deg + (lon_min / 60.0)
                    if parts[6] == 'W':
                        lon = -lon
                    
                    # Speed (knots to km/h)
                    speed_knots = float(parts[7]) if parts[7] else 0.0
                    speed = speed_knots * 1.852
                    
                    # Heading
                    heading = float(parts[8]) if parts[8] else 0.0
                    
                    return {
                        'lat': lat,
                        'lon': lon,
                        'speed': speed,
                        'heading': heading
                    }
                except (ValueError, IndexError) as e:
                    print(f"Error parsing NMEA: {e}")
                    return None
        
        elif parts[0] == '$GPGGA':
            # Global Positioning System Fix Data
            if len(parts) >= 15 and parts[6] != '0':  # Valid fix
                try:
                    # Latitude
                    lat_deg = float(parts[2][:2])
                    lat_min = float(parts[2][2:])
                    lat = lat_deg + (lat_min / 60.0)
                    if parts[3] == 'S':
                        lat = -lat
                    
                    # Longitude
                    lon_deg = float(parts[4][:3])
                    lon_min = float(parts[4][3:])
                    lon = lon_deg + (lon_min / 60.0)
                    if parts[5] == 'W':
                        lon = -lon
                    
                    return {
                        'lat': lat,
                        'lon': lon,
                        'speed': self.speed,  # Use previous speed
                        'heading': self.heading  # Use previous heading
                    }
                except (ValueError, IndexError) as e:
                    print(f"Error parsing NMEA: {e}")
                    return None
        
        return None
    
    def read_gps_data(self):
        """Read and parse GPS data from serial port"""
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
        
        try:
            line = self.serial_connection.readline().decode('utf-8', errors='ignore')
            if line:
                return self.parse_nmea_sentence(line)
        except Exception as e:
            print(f"Error reading GPS: {e}")
        
        return None
    
    def send_location_update(self):
        """Send location update to the server"""
        if self.lat is None or self.lon is None:
            return
        
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
                    "gps_fix_quality": "3D",
                    "satellites": 8,  # Would be read from actual GPS
                    "signal_strength": 95
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
        """Main GPS reading loop"""
        print(f"Starting GPS reader for Vehicle {self.vehicle_id}")
        print(f"Server URL: {self.server_url}")
        print(f"Serial Port: {self.serial_port}")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        if not self.connect_serial():
            return
        
        self.running = True
        last_update_time = 0
        update_interval = 5  # Send update every 5 seconds
        
        try:
            while self.running:
                gps_data = self.read_gps_data()
                
                if gps_data:
                    self.lat = gps_data['lat']
                    self.lon = gps_data['lon']
                    self.speed = gps_data['speed']
                    self.heading = gps_data['heading']
                    
                    # Send update at regular intervals
                    current_time = time.time()
                    if current_time - last_update_time >= update_interval:
                        self.send_location_update()
                        last_update_time = current_time
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
        except KeyboardInterrupt:
            print("\nStopping GPS reader...")
            self.running = False
        except Exception as e:
            print(f"GPS reader error: {e}")
            self.running = False
        finally:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()

def main():
    parser = argparse.ArgumentParser(description="Real GPS Reader for Vehicle Tracking")
    parser.add_argument("--vehicle-id", default="V001", help="Vehicle ID")
    parser.add_argument("--server-url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--serial-port", default="/dev/ttyUSB0", help="GPS Serial Port")
    parser.add_argument("--baud-rate", type=int, default=9600, help="Serial Baud Rate")
    
    args = parser.parse_args()
    
    reader = GPSReader(
        vehicle_id=args.vehicle_id,
        server_url=args.server_url,
        serial_port=args.serial_port,
        baud_rate=args.baud_rate
    )
    
    reader.run()

if __name__ == "__main__":
    main()