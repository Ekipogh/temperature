# SwitchBot 401 Authentication Error Fix

## 🐛 **Problem Description**

The Temperature Daemon was experiencing **401 Unauthorized errors after exactly 6 API requests** to SwitchBot devices. This issue appeared after implementing the `SwitchBotService` class and moving to Docker.

### **Symptoms:**
- First 6 requests to SwitchBot API work correctly
- Request #7 and beyond fail with 401 authentication errors
- Pattern was consistent and reproducible
- Affected both temperature and humidity readings

## 🔍 **Root Cause Analysis**

The issue was in the `SwitchBotService` class implementation:

### **Original Problematic Code:**
```python
class SwitchBotService:
    def __init__(self):
        self._bot = None  # Single instance, never recreated

    def connect(self, mac_address: str):
        if not self._bot:
            self._bot = SwitchBot(token=token, secret=secret)  # Created once
        device = self._bot.device(id=mac_address)
        return device
```

### **The Problem:**
1. **Single SwitchBot Instance**: The service created only one `SwitchBot(token, secret)` client and reused it indefinitely
2. **Token Expiration**: SwitchBot API tokens/sessions expire after a limited number of requests (6 in this case)
3. **No Refresh Mechanism**: The service never recreated the SwitchBot client when authentication failed
4. **Daemon Retry Logic**: The daemon tried to reinitialize the service, but it still used the same expired `_bot` instance

### **Why 6 Requests?**
The SwitchBot API appears to have a session-based authentication that expires after 6 successful requests, requiring a new authentication session.

## ✅ **Solution Implemented**

### **Enhanced SwitchBotService:**

1. **Connection State Tracking:**
   ```python
   def __init__(self):
       self._bot = None
       self._token = None
       self._secret = None
   ```

2. **Smart Connection Management:**
   ```python
   def connect(self, mac_address: str):
       # Recreate client if credentials changed or not initialized
       if not self._bot or self._token != token or self._secret != secret:
           logger.info("Creating new SwitchBot client instance")
           self._bot = SwitchBot(token=token, secret=secret)
           self._token = token
           self._secret = secret
   ```

3. **Authentication Error Recovery:**
   ```python
   def _reset_connection(self):
       """Reset the SwitchBot connection to force recreation on next request."""
       logger.info("Resetting SwitchBot connection due to authentication error")
       self._bot = None
       self._token = None
       self._secret = None
   ```

4. **Automatic Retry on 401 Errors:**
   ```python
   except Exception as e:
       if "401" in str(e) or "authentication" in error_str or "unauthorized" in error_str:
           self._reset_connection()
           # Try once more with fresh connection
           device = self.connect(mac_address)
           status = device.status()
           # ... handle response
   ```

## 🔧 **Key Improvements**

### **1. Automatic Authentication Recovery**
- Detects 401/authentication errors automatically
- Resets the SwitchBot client connection
- Retries the request once with a fresh authentication session

### **2. Connection State Management**
- Tracks current token/secret to detect changes
- Forces recreation of SwitchBot client when needed
- Logs connection reset events for debugging

### **3. Comprehensive Error Handling**
- Handles multiple error patterns: "401", "authentication", "unauthorized"
- Implements single retry to avoid infinite loops
- Graceful fallback if retry also fails

### **4. Simplified Daemon Logic**
- Removed complex service reinitialization from daemon
- Service now handles authentication internally
- Cleaner error handling in temperature collection

## 🧪 **Testing the Fix**

Use the provided test script to verify the fix:

```bash
# Test the authentication recovery
python test_auth_fix.py
```

**Expected Behavior:**
- ✅ **Before Fix**: Requests 1-6 succeed, requests 7+ fail with 401 errors
- ✅ **After Fix**: All requests succeed, with automatic recovery on authentication failures

## 📊 **Implementation Details**

### **Files Modified:**

1. **`services/switchbot_service.py`:**
   - Enhanced `SwitchBotService` class with connection state tracking
   - Added `_reset_connection()` method
   - Implemented automatic retry logic in all methods

2. **`scripts/temperature_daemon.py`:**
   - Simplified authentication error handling
   - Removed complex service reinitialization logic
   - Trust service to handle authentication internally

3. **`test_auth_fix.py`:**
   - Test script to verify the fix works
   - Makes 10 consecutive requests to trigger the scenario

### **Error Handling Flow:**

```
Request → SwitchBot API
    ↓
401 Error Detected
    ↓
Reset Connection (_reset_connection)
    ↓
Create Fresh SwitchBot Client
    ↓
Retry Request Once
    ↓
Success or Final Failure
```

## 🚀 **Deployment Instructions**

1. **Stop Current Daemon:**
   ```bash
   docker-compose -f ci/django-compose.production.yml down
   ```

2. **Rebuild with Fixed Code:**
   ```bash
   docker-compose -f ci/django-compose.production.yml build --no-cache
   ```

3. **Start Services:**
   ```bash
   docker-compose -f ci/django-compose.production.yml up -d
   ```

4. **Monitor Logs:**
   ```bash
   docker-compose -f ci/django-compose.production.yml logs -f temperature-daemon
   ```

**Look for Log Messages:**
- `"Creating new SwitchBot client instance"` - Normal connection creation
- `"Resetting SwitchBot connection due to authentication error"` - Recovery in action
- `"Authentication error getting temperature from [MAC], resetting connection"` - Error detection

## 📈 **Expected Results**

### **Before Fix:**
```
Request 1-6: ✅ Success
Request 7+:  ❌ 401 Unauthorized Error
```

### **After Fix:**
```
Request 1-6: ✅ Success
Request 7:   ❌ 401 Error → 🔄 Auto-retry → ✅ Success
Request 8+:  ✅ Success (with fresh auth session)
```

## 🔍 **Monitoring & Troubleshooting**

### **Success Indicators:**
- No more patterns of 6 successful requests followed by failures
- Log messages showing connection resets and recoveries
- Continuous temperature data collection without interruption

### **If Issues Persist:**
1. Check SwitchBot API credentials are valid
2. Verify network connectivity from Docker containers
3. Monitor for any new error patterns in logs
4. Consider rate limiting if API calls are too frequent

### **Debugging Commands:**
```bash
# Check daemon logs
docker-compose -f ci/django-compose.production.yml logs temperature-daemon

# Test authentication manually
python test_auth_fix.py

# Monitor API patterns
docker-compose -f ci/django-compose.production.yml logs temperature-daemon | grep -E "(401|authentication|Resetting)"
```

This fix addresses the core authentication session management issue and should resolve the 401 errors after 6 requests permanently.