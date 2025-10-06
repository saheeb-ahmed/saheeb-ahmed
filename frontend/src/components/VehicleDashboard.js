import React, { useState, useEffect } from 'react';
import { MapPin, Battery, Gauge, Clock, Navigation } from 'lucide-react';

const VehicleDashboard = ({ 
  vehicles, 
  selectedVehicle, 
  onVehicleSelect, 
  onCommandSend,
  onHistoryFetch 
}) => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    if (selectedVehicle) {
      onHistoryFetch(selectedVehicle.vehicle_id);
    }
  }, [selectedVehicle, onHistoryFetch]);

  const getBatteryColor = (level) => {
    if (level > 50) return '';
    if (level > 20) return 'low';
    return 'critical';
  };

  const formatSpeed = (speed) => {
    return speed ? `${speed.toFixed(1)} km/h` : '0 km/h';
  };

  const formatBattery = (level) => {
    return level ? `${level.toFixed(1)}%` : '100%';
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp).toLocaleDateString();
  };

  return (
    <div className="dashboard-container">
      <div className="vehicle-list">
        <h3>Vehicles ({vehicles.length})</h3>
        {vehicles.map(vehicle => (
          <div
            key={vehicle.vehicle_id}
            className={`vehicle-item ${selectedVehicle?.vehicle_id === vehicle.vehicle_id ? 'selected' : ''}`}
            onClick={() => onVehicleSelect(vehicle)}
          >
            <div className="vehicle-header">
              <span className="vehicle-id">Vehicle {vehicle.vehicle_id}</span>
              <span className={`vehicle-status ${vehicle.status}`}>
                {vehicle.status}
              </span>
            </div>
            
            <div className="vehicle-stats">
              <div className="stat-item">
                <div className="stat-label">
                  <MapPin size={14} /> Location
                </div>
                <div className="stat-value">
                  {vehicle.lat?.toFixed(6)}, {vehicle.lon?.toFixed(6)}
                </div>
              </div>
              
              <div className="stat-item">
                <div className="stat-label">
                  <Gauge size={14} /> Speed
                </div>
                <div className="stat-value">
                  {formatSpeed(vehicle.speed)}
                </div>
              </div>
              
              <div className="stat-item">
                <div className="stat-label">
                  <Navigation size={14} /> Heading
                </div>
                <div className="stat-value">
                  {vehicle.heading?.toFixed(1) || 0}°
                </div>
              </div>
              
              <div className="stat-item">
                <div className="stat-label">
                  <Battery size={14} /> Battery
                </div>
                <div className="battery-indicator">
                  <div className="battery-bar">
                    <div 
                      className={`battery-fill ${getBatteryColor(vehicle.battery_level)}`}
                      style={{ width: `${vehicle.battery_level || 100}%` }}
                    ></div>
                  </div>
                  <span>{formatBattery(vehicle.battery_level)}</span>
                </div>
              </div>
            </div>
            
            <div className="stat-item">
              <div className="stat-label">
                <Clock size={14} /> Last Update
              </div>
              <div className="stat-value">
                {formatTime(vehicle.last_update)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedVehicle && (
        <>
          <div className="command-panel">
            <h3>Vehicle Controls</h3>
            <p>Selected: Vehicle {selectedVehicle.vehicle_id}</p>
            
            <div className="command-buttons">
              <button 
                className="command-btn"
                onClick={() => onCommandSend('start')}
                disabled={selectedVehicle.status === 'active'}
              >
                Start Vehicle
              </button>
              
              <button 
                className="command-btn danger"
                onClick={() => onCommandSend('stop')}
                disabled={selectedVehicle.status !== 'active'}
              >
                Stop Vehicle
              </button>
              
              <button 
                className="command-btn"
                onClick={() => onCommandSend('return_home')}
              >
                Return Home
              </button>
              
              <button 
                className="command-btn"
                onClick={() => onCommandSend('emergency_stop')}
              >
                Emergency Stop
              </button>
            </div>
          </div>

          <div className="history-panel">
            <h3>Recent History</h3>
            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
              {vehicles
                .filter(v => v.vehicle_id === selectedVehicle.vehicle_id)
                .map(vehicle => (
                  <div key={vehicle.vehicle_id} className="history-item">
                    <div>
                      <div className="history-location">
                        {vehicle.lat?.toFixed(4)}, {vehicle.lon?.toFixed(4)}
                      </div>
                      <div className="history-time">
                        {formatDate(vehicle.last_update)} {formatTime(vehicle.last_update)}
                      </div>
                    </div>
                    <div>
                      {formatSpeed(vehicle.speed)} | {formatBattery(vehicle.battery_level)}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default VehicleDashboard;