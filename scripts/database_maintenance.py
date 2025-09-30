#!/usr/bin/env python3
"""
Database maintenance script for temperature monitoring system.
Provides utilities for analyzing, optimizing, and maintaining the database.
"""

import os
import sys
import django
from pathlib import Path
from django.db import connection
from datetime import datetime, timedelta
import sqlite3

# Setup Django
project_dir = Path(__file__).parent
sys.path.append(str(project_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'temperature.settings')
django.setup()

from homepage.models import Temperature

class DatabaseMaintenance:
    def __init__(self):
        self.db_path = Path(__file__).parent / 'db.sqlite3'
    
    def get_database_stats(self):
        """Get comprehensive database statistics."""
        stats = {}
        
        # Basic record counts
        stats['total_records'] = Temperature.objects.count()
        
        if stats['total_records'] > 0:
            # Date range
            first_record = Temperature.objects.earliest('timestamp')
            last_record = Temperature.objects.latest('timestamp')
            stats['first_record'] = first_record.timestamp
            stats['last_record'] = last_record.timestamp
            stats['date_range_days'] = (last_record.timestamp - first_record.timestamp).days
            
            # Records per location
            locations = Temperature.objects.values('location').distinct()
            for loc in locations:
                location_name = loc['location']
                count = Temperature.objects.filter(location=location_name).count()
                stats[f'records_{location_name.lower().replace(" ", "_")}'] = count
        
        # File size
        if self.db_path.exists():
            stats['file_size_bytes'] = self.db_path.stat().st_size
            stats['file_size_mb'] = stats['file_size_bytes'] / (1024 * 1024)
        
        return stats
    
    def print_stats(self):
        """Print formatted database statistics."""
        stats = self.get_database_stats()
        
        print("=" * 50)
        print("DATABASE STATISTICS")
        print("=" * 50)
        print(f"Total Records: {stats['total_records']:,}")
        print(f"Database Size: {stats.get('file_size_mb', 0):.2f} MB")
        
        if stats['total_records'] > 0:
            print(f"Date Range: {stats['date_range_days']} days")
            print(f"First Record: {stats['first_record']}")
            print(f"Last Record: {stats['last_record']}")
            
            avg_bytes_per_record = stats.get('file_size_bytes', 0) / stats['total_records']
            print(f"Avg Bytes/Record: {avg_bytes_per_record:.0f}")
            
            # Records per day
            if stats['date_range_days'] > 0:
                records_per_day = stats['total_records'] / stats['date_range_days']
                print(f"Avg Records/Day: {records_per_day:.1f}")
        
        print("\n" + "=" * 50)
        print("LOCATION BREAKDOWN")
        print("=" * 50)
        for key, value in stats.items():
            if key.startswith('records_'):
                location = key.replace('records_', '').replace('_', ' ').title()
                print(f"{location}: {value:,} records")
    
    def project_future_size(self, years=50):
        """Project future database size."""
        stats = self.get_database_stats()
        
        if stats['total_records'] == 0 or stats.get('date_range_days', 0) == 0:
            print("No data to project from")
            return
        
        # Calculate current rate
        records_per_day = stats['total_records'] / stats['date_range_days']
        bytes_per_record = stats.get('file_size_bytes', 0) / stats['total_records']
        
        print(f"\nFUTURE SIZE PROJECTIONS")
        print(f"Based on current rate: {records_per_day:.1f} records/day")
        print("=" * 60)
        
        periods = [1, 5, 10, 20, 50]
        for year in periods:
            future_records = int(records_per_day * 365 * year)
            future_size_mb = (future_records * bytes_per_record) / (1024 * 1024)
            future_size_gb = future_size_mb / 1024
            
            status = "✅" if future_size_gb < 1 else "⚠️" if future_size_gb < 5 else "❌"
            print(f"{year:2d} years: {future_records:,} records, "
                  f"{future_size_mb:,.0f} MB ({future_size_gb:.1f} GB) {status}")
    
    def optimize_database(self):
        """Optimize database performance."""
        print("Optimizing database...")
        
        with connection.cursor() as cursor:
            # Add indexes if they don't exist
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_temperature_timestamp ON homepage_temperature(timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_temperature_location ON homepage_temperature(location);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_temperature_location_timestamp ON homepage_temperature(location, timestamp);")
                print("✅ Indexes created/verified")
            except Exception as e:
                print(f"❌ Error creating indexes: {e}")
            
            # Vacuum database
            try:
                cursor.execute("VACUUM;")
                print("✅ Database vacuumed")
            except Exception as e:
                print(f"❌ Error vacuuming database: {e}")
            
            # Analyze database
            try:
                cursor.execute("ANALYZE;")
                print("✅ Database analyzed")
            except Exception as e:
                print(f"❌ Error analyzing database: {e}")
    
    def cleanup_old_data(self, days_to_keep=365):
        """Remove data older than specified days (use with caution!)."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        old_records = Temperature.objects.filter(timestamp__lt=cutoff_date)
        count = old_records.count()
        
        if count == 0:
            print(f"No records older than {days_to_keep} days found")
            return
        
        print(f"Found {count} records older than {days_to_keep} days")
        response = input(f"Delete these {count} records? (yes/no): ")
        
        if response.lower() == 'yes':
            old_records.delete()
            print(f"✅ Deleted {count} old records")
            self.optimize_database()
        else:
            print("❌ Cleanup cancelled")

def main():
    """Main function with command line interface."""
    maintenance = DatabaseMaintenance()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'stats':
            maintenance.print_stats()
        elif command == 'project':
            maintenance.print_stats()
            maintenance.project_future_size()
        elif command == 'optimize':
            maintenance.optimize_database()
        elif command == 'cleanup':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
            maintenance.cleanup_old_data(days)
        else:
            print("Usage: python database_maintenance.py [stats|project|optimize|cleanup [days]]")
    else:
        # Default: show stats and projections
        maintenance.print_stats()
        maintenance.project_future_size()

if __name__ == "__main__":
    main()