# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-06

### Added
- **SwitchBotService Class**: New service layer for SwitchBot API interactions
  - Encapsulates device connection and data retrieval
  - Consistent error handling and logging
  - Better separation of concerns
- **Docker Support**: Complete containerized deployment
  - Docker Compose configuration for pre-production environment
  - Separate containers for Django app and temperature daemon
  - Shared data volumes for database persistence
  - Health checks and automatic restarts
- **Optimized Refresh Strategy**: Two-tier refresh system
  - Manual refresh: Fetches fresh data from SwitchBot devices
  - Auto refresh: Fast database-only updates every 5 minutes
  - Reduced API calls and improved user experience
- **Enhanced Configuration**: Environment-based settings
  - Configurable database path via `DATABASE_PATH`
  - Extended daemon configuration options
  - Docker-specific environment variables

### Changed
- **Database Location**: Moved from root directory to `data/` subdirectory
  - Better organization and Docker volume management
  - Automatic migration of existing database
  - Configurable via environment variables
- **Daemon Architecture**: Refactored to use SwitchBotService
  - Cleaner code structure and better maintainability
  - Improved error handling and recovery
  - Enhanced rate limiting with exponential backoff
- **API Endpoints**: Updated to support optimized refresh
  - `/api/temperature/` for database-only queries
  - `/api/temperature/?manual=true` for device polling
  - Better performance and reduced API usage

### Enhanced
- **Error Handling**: Comprehensive error recovery
  - Authentication error handling with service reinitialization
  - Rate limiting with exponential backoff
  - Graceful degradation on device failures
- **Logging**: Improved logging throughout the system
  - Better error messages and debugging information
  - Structured logging for Docker environments
  - Enhanced daemon status monitoring
- **Frontend**: Optimized dashboard performance
  - Smart refresh strategies
  - Better loading states and user feedback
  - Responsive design improvements

### Fixed
- **Django Settings**: Proper database path configuration
- **Docker Build**: Fixed dependency installation and gunicorn setup
- **Port Consistency**: Aligned Docker and application port configurations
- **Environment Loading**: Improved .env file handling

### Technical Details

#### SwitchBotService Implementation
```python
class SwitchBotService:
    """Service for interacting with SwitchBot devices."""
    def get_temperature(self, mac_address: str) -> Optional[float]
    def get_humidity(self, mac_address: str) -> Optional[float]
```

#### Docker Architecture
- **Django Container**: Web dashboard on port 7070 (pre-prod)
- **Daemon Container**: Background data collection
- **Shared Volumes**: Database and logs persistence
- **Health Monitoring**: Automatic restart on failure

#### Database Changes
- **Location**: `data/db.sqlite3` (was `db.sqlite3`)
- **Configuration**: `DATABASE_PATH` environment variable
- **Migration**: Automatic on first run

#### Environment Variables
```env
# New variables added
TEMPERATURE_INTERVAL=600
RATE_LIMIT_SLEEP_TIME=300
DATABASE_PATH=/app/data/db.sqlite3
ENVIRONMENT=preprod
```

### Breaking Changes
- Database moved to `data/` directory (automatic migration provided)
- Daemon initialization process changed (uses SwitchBotService)
- Docker deployment requires updated environment configuration

### Migration Guide
1. **Database**: Will be automatically moved to `data/` directory on first run
2. **Environment**: Update `.env` file with new variables
3. **Docker**: Use new Docker Compose configuration
4. **Custom Code**: Update any scripts using direct SwitchBot integration

---

## [1.0.0] - 2025-09-30

### Added
- Initial release of Temperature Monitor
- Django-based web dashboard
- SwitchBot device integration
- Temperature daemon for data collection
- Real-time charts and historical data
- SQLite database storage
- Backup and maintenance utilities

### Features
- Multi-device temperature and humidity monitoring
- Interactive web dashboard with Chart.js
- Automatic data collection every 5 minutes
- Historical data visualization (6H, 24H, 7D)
- Admin interface for data management
- Comprehensive error handling and logging