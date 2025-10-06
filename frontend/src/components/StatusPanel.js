import React from 'react';

const StatusPanel = ({ isConnected, lastUpdate, vehicleCount }) => {
  const formatLastUpdate = (date) => {
    if (!date) return 'Never';
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    return `${Math.floor(seconds / 3600)}h ago`;
  };

  return (
    <div className="status-indicator">
      <div className={`status-dot ${isConnected ? '' : 'disconnected'}`}></div>
      <span>
        {isConnected ? 'Connected' : 'Disconnected'} | 
        Vehicles: {vehicleCount} | 
        Last Update: {formatLastUpdate(lastUpdate)}
      </span>
    </div>
  );
};

export default StatusPanel;