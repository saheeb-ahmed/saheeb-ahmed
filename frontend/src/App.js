import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import { Icon } from 'leaflet';
// Note: WebSocket connection will be handled by the backend directly
import VehicleDashboard from './components/VehicleDashboard';
import StatusPanel from './components/StatusPanel';
import './App.css';

// Fix for default markers in react-leaflet
delete Icon.Default.prototype._getIconUrl;
Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

function App() {
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [vehicleHistory, setVehicleHistory] = useState({});
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    // Initialize WebSocket connection
    const socket = new WebSocket('ws://localhost:8000/ws');
    
    socket.onopen = () => {
      console.log('Connected to WebSocket');
      setIsConnected(true);
    };

    socket.onclose = () => {
      console.log('Disconnected from WebSocket');
      setIsConnected(false);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'location_update') {
        console.log('Location update received:', data.data);
        updateVehicleLocation(data.data);
      }
    };

    // Fetch initial data
    fetchLatestLocations();

    return () => {
      socket.close();
    };
  }, []);

  const fetchLatestLocations = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/latest_locations');
      const data = await response.json();
      setVehicles(data.vehicles);
      
      // Set first vehicle as selected by default
      if (data.vehicles.length > 0 && !selectedVehicle) {
        setSelectedVehicle(data.vehicles[0]);
        fetchVehicleHistory(data.vehicles[0].vehicle_id);
      }
    } catch (error) {
      console.error('Error fetching latest locations:', error);
    }
  };

  const fetchVehicleHistory = async (vehicleId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/history/${vehicleId}?limit=100`);
      const data = await response.json();
      setVehicleHistory(prev => ({
        ...prev,
        [vehicleId]: data.locations
      }));
    } catch (error) {
      console.error('Error fetching vehicle history:', error);
    }
  };

  const updateVehicleLocation = (locationData) => {
    setVehicles(prevVehicles => {
      const updatedVehicles = prevVehicles.map(vehicle => 
        vehicle.vehicle_id === locationData.vehicle_id 
          ? { ...vehicle, ...locationData }
          : vehicle
      );
      
      // Add new vehicle if not exists
      if (!prevVehicles.find(v => v.vehicle_id === locationData.vehicle_id)) {
        updatedVehicles.push(locationData);
      }
      
      return updatedVehicles;
    });

    // Update history
    setVehicleHistory(prev => ({
      ...prev,
      [locationData.vehicle_id]: [
        locationData,
        ...(prev[locationData.vehicle_id] || []).slice(0, 99) // Keep last 100 points
      ]
    }));

    setLastUpdate(new Date());
  };

  const sendCommand = async (command, parameters = {}) => {
    if (!selectedVehicle) return;

    try {
      const response = await fetch('http://localhost:8000/api/send_command', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          vehicle_id: selectedVehicle.vehicle_id,
          command,
          parameters
        })
      });

      if (response.ok) {
        console.log(`Command sent: ${command}`);
      }
    } catch (error) {
      console.error('Error sending command:', error);
    }
  };

  const getVehicleIcon = (vehicle) => {
    const color = vehicle.status === 'active' ? 'green' : 'red';
    return new Icon({
      iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-${color}.png`,
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    });
  };

  const getRouteCoordinates = (vehicleId) => {
    const history = vehicleHistory[vehicleId] || [];
    return history
      .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      .map(point => [point.lat, point.lon]);
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>Autonomous Vehicle Tracker</h1>
        <StatusPanel 
          isConnected={isConnected} 
          lastUpdate={lastUpdate}
          vehicleCount={vehicles.length}
        />
      </header>
      
      <div className="app-content">
        <div className="map-container">
          <MapContainer
            center={[40.7128, -74.0060]} // Default to NYC
            zoom={13}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            {vehicles.map(vehicle => (
              <React.Fragment key={vehicle.vehicle_id}>
                <Marker
                  position={[vehicle.lat, vehicle.lon]}
                  icon={getVehicleIcon(vehicle)}
                >
                  <Popup>
                    <div>
                      <h3>Vehicle {vehicle.vehicle_id}</h3>
                      <p>Status: {vehicle.status}</p>
                      <p>Speed: {vehicle.speed?.toFixed(1) || 0} km/h</p>
                      <p>Battery: {vehicle.battery_level?.toFixed(1) || 0}%</p>
                      <p>Last Update: {new Date(vehicle.last_update).toLocaleString()}</p>
                    </div>
                  </Popup>
                </Marker>
                
                {vehicleHistory[vehicle.vehicle_id] && (
                  <Polyline
                    positions={getRouteCoordinates(vehicle.vehicle_id)}
                    color={vehicle.vehicle_id === selectedVehicle?.vehicle_id ? 'blue' : 'gray'}
                    weight={3}
                    opacity={0.7}
                  />
                )}
              </React.Fragment>
            ))}
          </MapContainer>
        </div>
        
        <div className="dashboard-container">
          <VehicleDashboard
            vehicles={vehicles}
            selectedVehicle={selectedVehicle}
            onVehicleSelect={setSelectedVehicle}
            onCommandSend={sendCommand}
            onHistoryFetch={fetchVehicleHistory}
          />
        </div>
      </div>
    </div>
  );
}

export default App;