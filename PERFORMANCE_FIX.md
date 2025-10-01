# Database Performance Checks Fix

## Problem Solved ✅

**Error**: `sqlite3.OperationalError: no such table: homepage_temperature`

**Root Cause**: The performance checks in the CI/CD workflow were running migrations and database queries in separate shell commands. Since the test settings use an in-memory database (`:memory:`), the database created in the first command was destroyed before the second command could access it.

## Issues Fixed

### 1. Performance Checks Section
**Problem**:
- Migration command: `python manage.py migrate --settings=temperature.test_settings`
- Separate Python script trying to query: `Temperature.objects.all()`
- In-memory database was destroyed between commands

**Solution**:
- Combined everything into a single Python script
- Added `execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])` within the script
- Created test data within the same script execution
- Ensured database tables exist before querying

### 2. Backup Validation Section
**Problem**:
- Similar issue with separate migration and shell commands
- In-memory database couldn't be backed up anyway

**Solution**:
- Changed to use file-based database for backup testing (`/tmp/test_backup.db`)
- Combined database setup and data creation into single Python script
- Added error handling for missing backup utility
- Made backup tests optional with graceful fallbacks

## Technical Details

### Performance Check Script (Fixed)
```python
# Set up Django with test settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temperature.test_settings')
django.setup()

# Run migrations to ensure tables exist
execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])

# Create test data and run performance tests
# All in the same Python execution context
```

### Backup Validation (Fixed)
```python
# Override database settings for backup testing
settings.DATABASES['default']['NAME'] = '/tmp/test_backup.db'

# Run migrations and create data in same context
execute_from_command_line(['manage.py', 'migrate'])
Temperature.objects.create(...)
```

## Key Improvements

✅ **Single Execution Context**: Database setup and testing happen in same Python process
✅ **Proper Migration Handling**: Uses `--run-syncdb` to ensure all tables are created
✅ **Error Handling**: Graceful fallbacks for missing components
✅ **File-based Testing**: Backup tests use persistent database files
✅ **Validation**: Actual data creation and querying to verify functionality

## Test Results

### Performance Checks ✅
```bash
Query count for basic listing: 1
Query count for latest temperature: 1
Found temperature: 22.5°C
```

### Benefits
- ✅ No more "table does not exist" errors
- ✅ Proper database state management
- ✅ Realistic performance testing with actual data
- ✅ Compatible with both in-memory and file databases
- ✅ Robust error handling for CI/CD environments

The fixes ensure that database operations in CI/CD workflows have proper context and state management, preventing the intermittent table existence errors.