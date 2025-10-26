# SwitchBot Hub WiFi Disconnection Detection

This document explains the various methods implemented to detect SwitchBot hub WiFi disconnections in your temperature daemon.

## 🔍 Detection Methods Implemented

### 1. **Network Ping Method** (Primary)
- **How it works**: Pings the SwitchBot hub's local IP address
- **Advantages**: Fast, reliable, detects network-level issues
- **Configuration**: Set `SWITCHBOT_HUB_IP` in your `.env` file
- **Example**: `SWITCHBOT_HUB_IP=192.168.1.100`

### 2. **API Connectivity Test** (Secondary)
- **How it works**: Makes a lightweight API call to test SwitchBot cloud service
- **Advantages**: Detects both local and cloud connectivity issues
- **No configuration needed**: Uses existing device configuration

### 3. **Combined Health Assessment**
- **How it works**: Combines both ping and API tests for comprehensive status
- **Status tracking**: Results stored in daemon status file
- **Monitoring**: Check `hub_connectivity` section in status JSON

## 🚀 Quick Setup

### Step 1: Find Your Hub IP
```bash
# Run the hub discovery tool
python find_switchbot_hub.py
```

### Step 2: Configure Environment
Add to your `.env` file:
```bash
# Replace with your actual hub IP
SWITCHBOT_HUB_IP=192.168.1.100

# Optional: Check connectivity every N iterations (default: 5)
CONNECTIVITY_CHECK_INTERVAL=5
```

### Step 3: Monitor Status
The daemon status file now includes connectivity information:
```json
{
  "hub_connectivity": {
    "hub_ping": true,
    "api_connectivity": true,
    "overall_healthy": true,
    "last_check": "2025-10-24T10:30:00"
  }
}
```

## 📊 Monitoring and Alerts

### Log Messages
- **Healthy**: `SwitchBot connectivity: All systems healthy`
- **Issues**: `SwitchBot connectivity issues: Hub ping: false, API: true`
- **Check frequency**: Every 5 daemon iterations (configurable)

### Status File Monitoring
Monitor the `daemon_status.json` file for connectivity changes:
```python
import json

def check_hub_status():
    with open('daemon_status.json') as f:
        status = json.load(f)

    connectivity = status.get('hub_connectivity', {})

    if not connectivity.get('overall_healthy'):
        print("🚨 SwitchBot hub connectivity issues detected!")
        print(f"Hub ping: {connectivity.get('hub_ping')}")
        print(f"API: {connectivity.get('api_connectivity')}")
```

## 🔧 Alternative Detection Methods

### Method 1: Router-based Monitoring
```bash
# Monitor DHCP lease table for hub MAC address
grep "SwitchBot" /var/lib/dhcp/dhcpd.leases
```

### Method 2: Network Scanning
```bash
# Use nmap to detect hub on network
nmap -sn 192.168.1.0/24 | grep -A2 -B2 "SwitchBot"
```

### Method 3: App Integration
- Check SwitchBot app for hub status
- Look for "Hub Offline" notifications
- Monitor app connectivity indicators

## 📱 Hub IP Discovery Methods

### Method 1: SwitchBot App
1. Open SwitchBot app
2. Go to Hub settings
3. Check "Device Info" or "Network Info"

### Method 2: Router Admin Panel
1. Login to your router (usually 192.168.1.1 or 192.168.0.1)
2. Check DHCP client list
3. Look for device named "SwitchBot" or similar

### Method 3: Network Scanner (provided)
```bash
python find_switchbot_hub.py
```

## 🚨 Troubleshooting

### Hub Not Responding to Ping
- **Check WiFi connection**: Hub may have lost WiFi
- **Check IP address**: Hub may have gotten new DHCP lease
- **Check router**: Network issues or router restart

### API Working but Ping Failing
- **Local network issue**: Hub connected to internet but not local network
- **Firewall**: Local firewall blocking ping
- **Network segmentation**: Hub on different VLAN

### Both Ping and API Failing
- **Complete disconnection**: Hub lost internet connectivity
- **Power issue**: Hub may be offline
- **Service outage**: SwitchBot cloud service down

## 📈 Performance Impact

- **Ping check**: ~1-3 seconds per check
- **API check**: ~2-5 seconds per check
- **Frequency**: Every 5 iterations by default (configurable)
- **Overall impact**: Minimal - checks run in background

## 🔄 Integration with Existing Features

The connectivity checks integrate seamlessly with existing daemon features:
- **Rate limiting**: Connectivity issues help explain API failures
- **Error handling**: Enhanced error context for troubleshooting
- **Status reporting**: Comprehensive health monitoring
- **Logging**: Detailed connectivity status in logs

## 💡 Best Practices

1. **Set realistic expectations**: Some temporary disconnections are normal
2. **Monitor trends**: Look for patterns in connectivity issues
3. **Combine with other monitoring**: Use with existing error tracking
4. **Regular maintenance**: Keep hub firmware updated
5. **Network stability**: Ensure stable WiFi coverage at hub location

## 🔮 Future Enhancements

Possible future improvements:
- Email/SMS alerts for prolonged disconnections
- Historical connectivity tracking
- Integration with home automation systems
- Predictive disconnection detection
- Automatic hub restart capabilities