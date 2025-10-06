# Deployment Guide

This guide covers deploying the Autonomous Vehicle Tracker system in various environments.

## Quick Start (Development)

### Prerequisites
- Docker and Docker Compose
- Git

### 1. Clone and Setup
```bash
git clone <repository-url>
cd autonomous-vehicle-tracker
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2. Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 3. Test the System
```bash
# Run API tests
python scripts/test_api.py

# Start GPS simulator
cd vehicle_client
python gps_simulator.py --vehicle-id V001
```

## Production Deployment

### 1. Server Requirements
- Ubuntu 20.04+ or CentOS 8+
- 4GB RAM minimum (8GB recommended)
- 50GB storage
- Public IP address
- Domain name (optional but recommended)

### 2. Environment Configuration

Create production environment file:
```bash
cp .env.example .env.prod
```

Edit `.env.prod`:
```env
# Database Configuration
MONGODB_URL=mongodb://admin:your-secure-password@mongodb:27017/vehicle_tracker?authSource=admin
REDIS_URL=redis://:your-redis-password@redis:6379

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production

# Security
SECRET_KEY=your-very-secure-secret-key-here
JWT_SECRET=your-jwt-secret-here

# CORS Configuration
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Vehicle Configuration
DEFAULT_UPDATE_INTERVAL=5
MAX_VEHICLES=100

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 3. SSL Certificate Setup

For production, obtain SSL certificates:

```bash
# Using Let's Encrypt (recommended)
sudo apt-get install certbot
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chown $USER:$USER nginx/ssl/*.pem
```

### 4. Deploy with Docker Compose

```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 5. Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow SSH (if needed)
sudo ufw allow 22

# Enable firewall
sudo ufw enable
```

## 4G Connectivity Setup

### Raspberry Pi Configuration

1. **Install Required Packages**
```bash
sudo apt-get update
sudo apt-get install ppp usb-modeswitch wvdial python3-pip
```

2. **Configure 4G Modem**
```bash
# Create wvdial configuration
sudo nano /etc/wvdial.conf
```

Example `wvdial.conf`:
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
Username = your-4g-username
Password = your-4g-password
```

3. **Start 4G Connection**
```bash
sudo wvdial
```

4. **Install Vehicle Client**
```bash
# Copy vehicle client to Pi
scp -r vehicle_client/ pi@raspberry-pi-ip:/home/pi/

# Install dependencies
ssh pi@raspberry-pi-ip
cd vehicle_client
pip3 install -r requirements.txt
```

5. **Run Vehicle Client**
```bash
# For real GPS
python3 real_gps_reader.py --vehicle-id V001 --server-url https://yourdomain.com

# For simulation
python3 gps_simulator.py --vehicle-id V001 --server-url https://yourdomain.com
```

## Monitoring and Maintenance

### 1. Health Checks

```bash
# Check application health
curl https://yourdomain.com/health

# Check API status
curl https://yourdomain.com/api/vehicles
```

### 2. Log Monitoring

```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f backend

# View all logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. Database Backup

```bash
# Backup MongoDB
docker exec vehicle_tracker_mongodb_prod mongodump --out /backup/$(date +%Y%m%d_%H%M%S)

# Restore from backup
docker exec vehicle_tracker_mongodb_prod mongorestore /backup/backup_folder
```

### 4. Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Fails**
   - Check CORS configuration
   - Verify WebSocket proxy settings in nginx
   - Check firewall rules

2. **GPS Data Not Updating**
   - Verify vehicle client connection
   - Check API endpoint accessibility
   - Verify MongoDB connection

3. **Map Not Loading**
   - Check Leaflet.js CDN access
   - Verify browser console for errors
   - Check CORS settings

4. **High Memory Usage**
   - Monitor container resources
   - Adjust memory limits in docker-compose
   - Check for memory leaks

### Performance Optimization

1. **Database Indexing**
```bash
# Connect to MongoDB
docker exec -it vehicle_tracker_mongodb_prod mongo

# Create indexes
use vehicle_tracker
db.locations.createIndex({"vehicle_id": 1, "timestamp": -1})
db.vehicle_status.createIndex({"vehicle_id": 1})
```

2. **Caching**
- Redis is already configured for caching
- Consider implementing API response caching
- Use CDN for static assets

3. **Load Balancing**
- Use multiple backend replicas
- Implement horizontal scaling
- Use load balancer for high availability

## Security Considerations

1. **Network Security**
   - Use HTTPS in production
   - Implement proper firewall rules
   - Use VPN for vehicle connections

2. **Authentication**
   - Implement API key authentication
   - Use JWT tokens for sessions
   - Add rate limiting

3. **Data Security**
   - Encrypt sensitive data
   - Regular security updates
   - Monitor for vulnerabilities

## Scaling

### Horizontal Scaling

1. **Multiple Backend Instances**
```yaml
# In docker-compose.prod.yml
backend:
  deploy:
    replicas: 3
```

2. **Load Balancer Configuration**
```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}
```

3. **Database Clustering**
- Use MongoDB replica set
- Implement read replicas
- Use Redis cluster for caching

## Backup and Recovery

### Automated Backups

Create backup script:
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/$DATE"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup MongoDB
docker exec vehicle_tracker_mongodb_prod mongodump --out $BACKUP_DIR/mongodb

# Backup Redis
docker exec vehicle_tracker_redis_prod redis-cli --rdb $BACKUP_DIR/redis.rdb

# Compress backup
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

# Keep only last 7 days of backups
find /backup -name "*.tar.gz" -mtime +7 -delete
```

Schedule with cron:
```bash
# Add to crontab
0 2 * * * /path/to/backup.sh
```

This completes the comprehensive deployment guide for the Autonomous Vehicle Tracker system.