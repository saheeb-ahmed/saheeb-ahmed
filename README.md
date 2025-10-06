# Autonomous Vehicle Tracker

A full-stack web application for real-time mapping and remote monitoring of autonomous vehicles. The system receives GPS location and telemetry data from a Raspberry Pi (connected over 4G modem), displays live vehicle position on a map, and enables data exchange between the vehicle and the website.

## Features

- **Real-time GPS Tracking**: Live vehicle position updates on an interactive map
- **Multi-vehicle Support**: Track multiple vehicles simultaneously
- **WebSocket Communication**: Real-time updates without polling
- **RESTful API**: Complete API for vehicle data management
- **Responsive Dashboard**: Modern UI with vehicle status and controls
- **Route History**: Visualize vehicle paths and journey history
- **Command System**: Send commands to vehicles remotely
- **Docker Support**: Easy deployment with Docker Compose

## System Architecture

- **Backend**: FastAPI (Python) with MongoDB
- **Frontend**: React.js with Leaflet.js maps
- **Database**: MongoDB for data storage
- **Real-time**: WebSocket connections
- **Deployment**: Docker containers

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.11+ (for development)

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd autonomous-vehicle-tracker
   ```

2. **Start the services**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development Setup

1. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Start MongoDB (using Docker)
   docker run -d -p 27017:27017 --name mongodb mongo:7.0
   
   # Start the backend
   cd backend
   python main.py
   ```

2. **Frontend Setup**
   ```bash
   # Install Node.js dependencies
   cd frontend
   npm install
   
   # Start the development server
   npm start
   ```

3. **Vehicle Client Setup**
   ```bash
   # Install Python dependencies
   cd vehicle_client
   pip install -r requirements.txt
   
   # Run GPS simulator
   python gps_simulator.py --vehicle-id V001
   
   # Or run real GPS reader (Raspberry Pi)
   python real_gps_reader.py --vehicle-id V001 --serial-port /dev/ttyUSB0
   ```

## API Endpoints

### Location Updates
- `POST /api/update_location` - Update vehicle location
- `GET /api/latest_location/{vehicle_id}` - Get latest location
- `GET /api/latest_locations` - Get all latest locations
- `GET /api/history/{vehicle_id}` - Get location history

### Vehicle Management
- `GET /api/vehicles` - List all vehicles
- `POST /api/send_command` - Send command to vehicle

### WebSocket
- `WS /ws` - Real-time updates

## Vehicle Client

The system includes two vehicle client options:

### 1. GPS Simulator
Simulates a vehicle with realistic movement patterns:
```bash
python vehicle_client/gps_simulator.py --vehicle-id V001 --server-url http://localhost:8000
```

### 2. Real GPS Reader
For actual Raspberry Pi with GPS module:
```bash
python vehicle_client/real_gps_reader.py --vehicle-id V001 --serial-port /dev/ttyUSB0
```

## Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Key configuration options:
- `MONGODB_URL`: MongoDB connection string
- `REDIS_URL`: Redis connection string
- `ALLOWED_ORIGINS`: CORS allowed origins
- `SECRET_KEY`: Application secret key

## Deployment

### Production Deployment

1. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Set up reverse proxy (Nginx)**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://localhost:3000;
       }
       
       location /api {
           proxy_pass http://localhost:8000;
       }
       
       location /ws {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

### 4G Connectivity

For 4G connectivity on Raspberry Pi:

1. **Configure 4G modem**
   ```bash
   # Install required packages
   sudo apt-get update
   sudo apt-get install ppp usb-modeswitch wvdial
   
   # Configure wvdial
   sudo nano /etc/wvdial.conf
   ```

2. **Example wvdial.conf**
   ```ini
   [Dialer Defaults]
   Init1 = ATZ
   Init2 = ATQ0 V1 E1 S0=0 &C1 &D2 +FCLASS=0
   Modem Type = Analog Modem
   Baud = 460800
   New PPPD = yes
   Modem = /dev/ttyUSB0
   ISDN = 0
   Phone = *99#
   Username = your-username
   Password = your-password
   ```

3. **Start connection**
   ```bash
   sudo wvdial
   ```

## Security Considerations

- Use HTTPS in production
- Implement authentication for vehicle clients
- Validate all incoming data
- Use environment variables for secrets
- Regular security updates

## Monitoring

The system includes health check endpoints:
- `GET /health` - Application health status
- `GET /api/vehicles` - Vehicle status overview

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**
   - Check CORS configuration
   - Verify WebSocket proxy settings

2. **GPS data not updating**
   - Check vehicle client connection
   - Verify API endpoint accessibility
   - Check MongoDB connection

3. **Map not loading**
   - Verify Leaflet.js CDN access
   - Check browser console for errors

### Logs

View application logs:
```bash
# Docker logs
docker-compose logs -f backend

# Application logs
tail -f logs/app.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API documentation at `/docs`