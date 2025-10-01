# Temperature Monitor

A Django-based temperature monitoring system that collects data from SwitchBot devices and displays it in a beautiful web dashboard.

[![CI/CD](../../actions/workflows/ci-cd.yml/badge.svg)](../../actions/workflows/ci-cd.yml)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](#requirements)
[![Django](https://img.shields.io/badge/django-5.2-green.svg)](#requirements)

## Features

- 🌡️ **Real-time Temperature Monitoring** - Collect temperature and humidity data from multiple SwitchBot devices
- 📊 **Interactive Dashboard** - Beautiful web interface with real-time charts and current readings
- 🔄 **Automatic Data Collection** - Background daemon continuously collects data every 5 minutes
- 📈 **Historical Data** - View temperature trends over time (6H, 24H, 7D views)
- 🗄️ **Database Storage** - Efficient SQLite storage with proper indexing
- 🛡️ **Data Validation** - Comprehensive input validation and error handling
- 📱 **Responsive Design** - Works on desktop and mobile devices
- 🔧 **Maintenance Tools** - Built-in backup and database maintenance utilities

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

# Data collection interval in seconds (default: 300 = 5 minutes)
TEMPERATURE_INTERVAL=300
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

- `GET /api/temperature/` - Current temperature readings
- `GET /api/temperature/?manual=true` - Refresh from devices and return current readings
- `GET /api/historical/?hours=24` - Historical data for specified hours

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
- Check Django server is running on port 8000
- Verify `ALLOWED_HOSTS` setting
- Check browser console for JavaScript errors

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

---

Made with ❤️ for home automation enthusiasts