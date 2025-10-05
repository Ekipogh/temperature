# Temperature Monitor

A Django-based temperature monitoring system that   Open http://localhost:8000 in your browser

## Architecture

### System Components

**SwitchBotService Class**
- Encapsulates all SwitchBot API interactions
- Handles device connection and data retrieval
- Provides consistent error handling and logging
- Used by both daemon and web application

**Temperature Daemon (Enhanced)**
- Service-oriented architecture using SwitchBotService
- Exponential backoff for rate limiting
- Comprehensive error handling and recovery
- Health monitoring and status reporting
- Configurable collection intervals

**Django Web Application**
- Real-time dashboard with Vue.js frontend
- Optimized API endpoints with caching
- Separate manual vs automatic refresh
- Database storage in configurable location

**Database Architecture**
- SQLite database stored in `data/` directory
- Shared between daemon and web application
- Automatic backup and maintenance utilities
- Configurable location via environment variables

### Data Flow

1. **Background Collection**: Daemon collects data every 10 minutes
2. **Database Storage**: Data stored in shared SQLite database
3. **Web Dashboard**: Displays real-time data and historical charts
4. **Manual Refresh**: Users can trigger immediate device polling
5. **Auto Refresh**: Dashboard updates from database every 5 minutes

## Configurationllects data from SwitchBot devices and displays it in a beautiful web dashboard.

[![CI/CD](../../actions/workflows/ci-cd.yml/badge.svg)](../../actions/workflows/ci-cd.yml)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](#requirements)
[![Django](https://img.shields.io/badge/django-5.2-green.svg)](#requirements)

## Features

- 🌡️ **Real-time Temperature Monitoring** - Collect temperature and humidity data from multiple SwitchBot devices
- 📊 **Interactive Dashboard** - Beautiful web interface with real-time charts and current readings
- 🔄 **Smart Data Collection** - Background daemon with rate limiting and error recovery
- 📈 **Historical Data** - View temperature trends over time (6H, 24H, 7D views)
- 🗄️ **Database Storage** - Efficient SQLite storage with configurable location
- 🛡️ **Data Validation** - Comprehensive input validation and error handling
- 📱 **Responsive Design** - Works on desktop and mobile devices
- 🔧 **Maintenance Tools** - Built-in backup and database maintenance utilities
- 🐳 **Docker Support** - Complete containerized deployment with Docker Compose
- ⚡ **Optimized Refresh** - Separate manual vs automatic refresh strategies
- 🏗️ **Service Architecture** - Clean separation of concerns with SwitchBotService class

## Screenshots

![Dashboard](docs/dashboard.png)
*Main dashboard showing current temperatures and historical charts*

## Quick Start

### Prerequisites

- Python 3.9 or higher
- SwitchBot devices with API access
- SwitchBot app with Developer Mode enabled

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd temperature
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your SwitchBot credentials and device MAC addresses
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Start the web server**
   ```bash
   python manage.py runserver
   ```

7. **Start the data collection daemon** (in another terminal)
   ```bash
   python scripts/temperature_daemon.py
   ```

8. **Access the dashboard**
   - Open http://localhost:8000 in your browser

## Docker Deployment

### Pre-production Environment

For a complete containerized deployment with automatic restarts and shared data volumes:

1. **Prepare environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your SwitchBot credentials
   ```

2. **Deploy with Docker Compose**
   ```bash
   cd ci
   docker-compose -f docker-compose.preprod.yml up -d
   ```

3. **Access the dashboard**
   - Pre-prod environment: http://localhost:7070

📖 **For detailed Docker deployment instructions, see [Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md)**

### Docker Architecture

- **Django Application Container**: Web dashboard and API endpoints
- **Temperature Daemon Container**: Background data collection service
- **Shared Data Volume**: Database and logs persistence
- **Health Checks**: Automatic container monitoring and restart
- **Network Isolation**: Containers communicate via internal Docker network

### Docker Features

- 🔄 **Automatic Restarts**: Containers restart on failure
- 📊 **Health Monitoring**: Built-in health checks for both services
- 💾 **Data Persistence**: Database and logs survive container restarts
- 🔒 **Security**: Non-root user execution in containers
- 🎛️ **Environment Configuration**: Configurable via environment variables
- 📈 **Scalability**: Separate containers for web and data collection

### Container Environment Variables

```env
# Required for both containers
SWITCHBOT_TOKEN=your_token_here
SWITCHBOT_SECRET=your_secret_here

# Daemon-specific settings
TEMPERATURE_INTERVAL=600  # Data collection interval (seconds)
RATE_LIMIT_SLEEP_TIME=300 # Rate limit backoff (seconds)
DATABASE_PATH=/app/data/db.sqlite3  # Database location in container
ENVIRONMENT=preprod  # Environment identifier

# Device MAC addresses
LIVING_ROOM_MAC=D40E84863006
BEDROOM_MAC=D40E84861814
OFFICE_MAC=D628EA1C498F
OUTDOOR_MAC=D40E84064570
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# SwitchBot API Credentials (get from SwitchBot app)
SWITCHBOT_TOKEN=your_switchbot_token_here
SWITCHBOT_SECRET=your_switchbot_secret_here

# Device MAC Addresses
LIVING_ROOM_MAC=D40E84863006
BEDROOM_MAC=D40E84861814
OFFICE_MAC=D628EA1C498F
OUTDOOR_MAC=D40E84064570

# Data collection settings
TEMPERATURE_INTERVAL=600  # Collection interval in seconds (default: 10 minutes)
RATE_LIMIT_SLEEP_TIME=300 # Rate limit backoff in seconds (default: 5 minutes)

# Database configuration
DATABASE_PATH=data/db.sqlite3  # Database file location (default: data/db.sqlite3)

# Docker-specific (optional)
ENVIRONMENT=development  # Environment identifier
```

### Getting SwitchBot Credentials

1. Open the SwitchBot app
2. Go to Profile > Preference
3. Tap "App Version" 10 times to enable Developer Options
4. Go to Developer Options
5. Copy your Token and Secret

## Usage

### Dashboard Features

- **Current Readings**: Real-time temperature and humidity for each location
- **Historical Charts**: Interactive charts showing temperature trends
- **Time Range Selection**: View data for 6H, 24H, or 7 days
- **Auto-refresh**: Dashboard automatically updates every 5 minutes
- **Manual Refresh**: Click refresh button to fetch fresh data from devices

### API Endpoints

- `GET /api/temperature/` - Current temperature readings (database only)
- `GET /api/temperature/?manual=true` - Refresh from devices and return current readings
- `GET /api/historical/?hours=24` - Historical data for specified hours

### Dashboard Refresh Strategy

The dashboard now uses an optimized two-tier refresh strategy:

**Automatic Refresh (Every 5 minutes)**
- Fetches data from database only
- No SwitchBot API calls
- Fast and efficient
- Runs in background without loading spinner

**Manual Refresh (User-triggered)**
- Fetches fresh data from SwitchBot devices
- Updates database with latest readings
- Shows loading spinner during fetch
- Resets automatic refresh timer

This approach reduces API calls while maintaining real-time updates through the background daemon.

### Maintenance

#### Database Backup
```bash
python backup_utility.py create
```

#### Database Statistics
```bash
python database_maintenance.py stats
```

#### Optimize Database
```bash
python database_maintenance.py optimize
```

## Testing

### Run All Tests
```bash
python manage.py test --settings=temperature.test_settings
```

### Run Specific Test Categories
```bash
# Model tests
python manage.py test homepage.tests.TemperatureModelTests --settings=temperature.test_settings

# View tests
python manage.py test homepage.tests.TemperatureViewTests --settings=temperature.test_settings

# Daemon tests
python manage.py test homepage.test_daemon --settings=temperature.test_settings
```

### Test Coverage
```bash
pip install pytest pytest-django pytest-cov
pytest --cov=homepage --cov=scripts --cov-report=html
```

## Development

### Project Structure
```
temperature/
├── homepage/           # Main Django app
│   ├── models.py       # Temperature data model
│   ├── views.py        # API and web views
│   ├── tests.py        # Comprehensive tests
│   └── templates/      # Web dashboard templates
├── scripts/            # Background services
│   └── temperature_daemon.py  # Data collection daemon
├── temperature/        # Django project settings
├── .gitea/workflows/   # CI/CD workflows
├── manage.py           # Django management script
├── backup_utility.py   # Database backup tools
└── database_maintenance.py  # Database maintenance tools
```

### Adding New Locations

1. Add device MAC address to `.env`
2. Update `device_configs` in `temperature_daemon.py`
3. Update `location_map` in the daemon's `store_temperature` method
4. Add location to `unique_locations` list in `views.py`

### Database Schema

The `Temperature` model stores:
- `timestamp`: When the reading was taken
- `location`: Device location (Living Room, Bedroom, etc.)
- `temperature`: Temperature in Celsius (validated -50°C to 70°C)
- `humidity`: Relative humidity percentage (validated 0% to 100%)

## Deployment

### Production Checklist

- [ ] Set `DEBUG = False` in settings
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up environment variables securely
- [ ] Configure web server (nginx/Apache)
- [ ] Set up systemd service for daemon
- [ ] Configure database backups
- [ ] Set up monitoring and alerts

### Systemd Service

Create `/etc/systemd/system/temperature-daemon.service`:

```ini
[Unit]
Description=Temperature Monitor Daemon
After=network.target

[Service]
Type=simple
User=temperature
WorkingDirectory=/opt/temperature-monitor
Environment=PATH=/opt/temperature-monitor/.venv/bin
ExecStart=/opt/temperature-monitor/.venv/bin/python scripts/temperature_daemon.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Docker Deployment

A Dockerfile is included for containerized deployment:

```bash
docker build -t temperature-monitor .
docker run -d --env-file .env -p 8000:8000 temperature-monitor
```

## Monitoring and Alerts

### Health Checks

The daemon includes comprehensive error handling and logging:
- Authentication failures are automatically retried
- Device communication errors are logged and handled gracefully
- Consecutive failures trigger daemon shutdown with alerts

### Logs

- Daemon logs: `temperature_daemon.log`
- Django logs: Console output
- Backup logs: Included in backup utility output

## Docker Management

### Container Operations

**View running containers**
```bash
docker-compose -f ci/docker-compose.preprod.yml ps
```

**View logs**
```bash
# All services
docker-compose -f ci/docker-compose.preprod.yml logs -f

# Specific service
docker-compose -f ci/docker-compose.preprod.yml logs -f temperature-daemon
docker-compose -f ci/docker-compose.preprod.yml logs -f django-app
```

**Restart services**
```bash
# Restart all
docker-compose -f ci/docker-compose.preprod.yml restart

# Restart specific service
docker-compose -f ci/docker-compose.preprod.yml restart temperature-daemon
```

**Stop and remove**
```bash
docker-compose -f ci/docker-compose.preprod.yml down

# Remove volumes too (⚠️ deletes data)
docker-compose -f ci/docker-compose.preprod.yml down -v
```

**Rebuild containers**
```bash
docker-compose -f ci/docker-compose.preprod.yml build
docker-compose -f ci/docker-compose.preprod.yml up -d
```

### Health Monitoring

**Check container health**
```bash
docker inspect temperature_daemon_preprod | grep -A 5 "Health"
```

**Monitor daemon status**
```bash
docker exec temperature_daemon_preprod cat /app/daemon_status.json
```

### Data Management

**Access database**
```bash
docker exec -it django_app_preprod python manage.py shell
```

**Backup database**
```bash
docker exec django_app_preprod python backup_utility.py create
```

**View data directory**
```bash
docker exec django_app_preprod ls -la /app/data/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`python manage.py test`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use Black for code formatting: `black .`
- Use isort for import sorting: `isort .`
- Run flake8 for linting: `flake8 .`

## Troubleshooting

### Common Issues

**401 Authentication Error**
- Check SwitchBot token and secret in `.env`
- Ensure Developer Mode is enabled in SwitchBot app
- Verify the `.env` file is being loaded correctly

**No Data Appearing**
- Check if the daemon is running: `ps aux | grep temperature_daemon`
- Check daemon logs: `tail -f temperature_daemon.log`
- Verify device MAC addresses are correct

**Database Errors**
- Run migrations: `python manage.py migrate`
- Check database permissions
- Verify SQLite file exists and is writable

**Dashboard Not Loading**
- Check Django server is running on port 8000 (or 7070 for Docker)
- Verify `ALLOWED_HOSTS` setting
- Check browser console for JavaScript errors

**Docker Issues**
- Check container status: `docker-compose -f ci/docker-compose.preprod.yml ps`
- View container logs: `docker-compose -f ci/docker-compose.preprod.yml logs -f`
- Ensure `.env` file exists and is properly configured
- Check port conflicts (7070 for pre-prod, 8000 for local)
- Verify Docker volumes are properly mounted

**Service Architecture Issues**
- Check SwitchBotService initialization in logs
- Verify environment variables are loaded correctly
- Check daemon status file: `cat daemon_status.json`
- Monitor rate limiting in daemon logs

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [SwitchBot](https://www.switchbot.com/) for the temperature sensor devices
- [Django](https://www.djangoproject.com/) for the web framework
- [Chart.js](https://www.chartjs.org/) for the dashboard charts
- [Bootstrap](https://getbootstrap.com/) for the UI components

## Support

If you encounter any issues or have questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Search existing [issues](../../issues)
3. Create a new issue with detailed information
4. Include logs and configuration (remove sensitive data)

## Recent Changes

### v2.0.0 - Service Architecture & Docker Deployment

📋 **For complete change history, see [CHANGELOG.md](CHANGELOG.md)**

**Major Architecture Improvements:**
- ✅ **SwitchBotService Class**: New service layer for cleaner API interaction
- ✅ **Enhanced Daemon**: Improved error handling, rate limiting, and recovery
- ✅ **Docker Support**: Complete containerized deployment with Docker Compose
- ✅ **Database Relocation**: Database moved to `data/` directory for better organization
- ✅ **Optimized Refresh**: Separate manual vs automatic refresh strategies

**Technical Details:**

*SwitchBotService Implementation*
- Encapsulated all SwitchBot API calls in dedicated service class
- Improved error handling and logging consistency
- Better separation of concerns in daemon architecture
- Enhanced testability and maintainability

*Daemon Enhancements*
- Replaced direct SwitchBot integration with service layer
- Improved authentication error recovery
- Better device initialization with retry logic
- Enhanced rate limiting with exponential backoff

*Docker Deployment*
- Pre-production Docker Compose configuration
- Separate containers for web app and daemon
- Shared data volumes for database persistence
- Health checks and automatic restarts
- Environment-based configuration

*Database Architecture*
- Database moved from root to `data/` directory
- Configurable database path via `DATABASE_PATH` environment variable
- Automatic directory creation and migration
- Better Docker volume management

*Frontend Optimizations*
- Smart refresh strategy reduces API calls
- Manual refresh fetches from devices
- Auto refresh uses database only
- Improved user experience with loading states

**Breaking Changes:**
- Database location changed from root to `data/` directory
- Daemon now uses SwitchBotService instead of direct API calls
- Docker deployment requires environment variable updates

**Migration Guide:**
1. Update `.env` file with new environment variables
2. Database will be automatically moved to `data/` directory
3. Update any custom scripts to use new service architecture
4. Use Docker Compose for production deployments

---

Made with ❤️ for home automation enthusiasts