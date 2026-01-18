"""
Database Management Utility Script
===================================

Useful utilities for managing your SQLite vehicle detection database:
- View data statistics
- Export data
- Query by date range
- Backup database
- Clean old records
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import time
import sqlite3

# Add current and parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from secure_streaming import VehicleCountDatabase

# Default database path (in parent data subdirectory)
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'vehicle_detection.db')


def print_separator(title=""):
    """Print a formatted separator"""
    if title:
        print(f"\n{'='*60}")
        print(f"{title.center(60)}")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'-'*60}\n")


def view_database_info(db_path=None):
    """Display database information and statistics"""
    if db_path is None:
        db_path = DEFAULT_DB_PATH
        
    print_separator("DATABASE INFORMATION")
    
    if not os.path.exists(db_path):
        print(f" Database not found: {db_path}")
        print(f"   Expected location: {DEFAULT_DB_PATH}")
        return
    
    db = VehicleCountDatabase(db_path=db_path)
    
    total = db.get_total_records()
    print(f"Database file: {db_path}")
    print(f"File size: {os.path.getsize(db_path) / 1024:.1f} KB")
    print(f"Total records: {total}")
    
    if total == 0:
        print("(No data in database)")
        return
    
    latest = db.get_latest(limit=1)
    if latest:
        first_time = latest[0]['timestamp']
        oldest = db.db.get_latest_counts(limit=1)  # Will be oldest when ordered DESC
        print(f"Latest record: {latest[0]['datetime_str']}")
    
    print()


def view_statistics(db_path="vehicle_detection.db"):
    """Display database statistics"""
    print_separator("DATABASE STATISTICS")
    
    db = VehicleCountDatabase(db_path=db_path)
    stats = db.get_statistics()
    
    if stats['total_records'] == 0:
        print("No data in database")
        return
    
    print(f"Total Records: {stats['total_records']}")
    
    print("\n TOTALS:")
    print(f"  Cars:      {stats['total']['cars']:,}")
    print(f"  Vans:      {stats['total']['vans']:,}")
    print(f"  Motors:    {stats['total']['motors']:,}")
    print(f"  Buses:     {stats['total']['buses']:,}")
    print(f"  Bicycles:  {stats['total']['bicycles']:,}")
    
    print("\n AVERAGES PER RECORD:")
    print(f"  Cars:      {stats['average']['cars']:.1f}")
    print(f"  Vans:      {stats['average']['vans']:.1f}")
    print(f"  Motors:    {stats['average']['motors']:.1f}")
    print(f"  Buses:     {stats['average']['buses']:.1f}")
    print(f"  Bicycles:  {stats['average']['bicycles']:.1f}")
    
    print("\n  PEAKS (Maximum):")
    print(f"  Cars:      {stats['maximum']['cars']}")
    print(f"  Vans:      {stats['maximum']['vans']}")
    print(f"  Motors:    {stats['maximum']['motors']}")
    print(f"  Buses:     {stats['maximum']['buses']}")
    print(f"  Bicycles:  {stats['maximum']['bicycles']}")
    
    print("\n  MINIMUMS:")
    print(f"  Cars:      {stats['minimum']['cars']}")
    print(f"  Vans:      {stats['minimum']['vans']}")
    print(f"  Motors:    {stats['minimum']['motors']}")
    print(f"  Buses:     {stats['minimum']['buses']}")
    print(f"  Bicycles:  {stats['minimum']['bicycles']}")


def view_latest_records(db_path="vehicle_detection.db", limit=20):
    """Display latest records"""
    print_separator(f"LATEST {limit} RECORDS")
    
    db = VehicleCountDatabase(db_path=db_path)
    records = db.get_latest(limit=limit)
    
    if not records:
        print("No records found")
        return
    
    print(f"{'DateTime':<25} {'Cars':<6} {'Vans':<6} {'Motors':<7} {'Buses':<6} {'Bicycles':<8}")
    print("-" * 60)
    
    for record in records:
        print(f"{record['datetime_str']:<25} {record['cars']:<6} {record['vans']:<6} "
              f"{record['motors']:<7} {record['buses']:<6} {record['bicycles']:<8}")


def export_to_csv(db_path="vehicle_detection.db", output_file="vehicle_export.csv"):
    """Export database to CSV"""
    print_separator("EXPORT TO CSV")
    
    db = VehicleCountDatabase(db_path=db_path)
    
    if db.export_csv(output_file):
        file_size = os.path.getsize(output_file) / 1024
        print(f" Successfully exported to: {output_file}")
        print(f"   File size: {file_size:.1f} KB")
        print(f"\n   You can now open this file in:")
        print(f"   - Excel")
        print(f"   - Google Sheets")
        print(f"   - Pandas (Python): pd.read_csv('{output_file}')")
    else:
        print(" Export failed")


def backup_database(db_path="vehicle_detection.db"):
    """Create a backup of the database"""
    print_separator("BACKUP DATABASE")
    
    if not os.path.exists(db_path):
        print(f" Database not found: {db_path}")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"vehicle_detection_backup_{timestamp}.db"
    
    try:
        # Copy the database file
        with open(db_path, 'rb') as src:
            with open(backup_file, 'wb') as dst:
                dst.write(src.read())
        
        backup_size = os.path.getsize(backup_file) / 1024
        print(f" Backup created: {backup_file}")
        print(f"   Size: {backup_size:.1f} KB")
        print(f"\nTo restore this backup later:")
        print(f"   cp {backup_file} {db_path}")
    except Exception as e:
        print(f" Backup failed: {str(e)}")


def clean_old_records(db_path="vehicle_detection.db", days=30):
    """Delete records older than specified days"""
    print_separator("CLEAN OLD RECORDS")
    
    db = VehicleCountDatabase(db_path=db_path)
    
    total_before = db.get_total_records()
    deleted = db.clear_old_records(days_to_keep=days)
    total_after = db.get_total_records()
    
    print(f"Records before: {total_before}")
    print(f"Records deleted: {deleted}")
    print(f"Records after: {total_after}")
    
    if deleted > 0:
        print(f"\n Deleted {deleted} records older than {days} days")
    else:
        print(f"\nℹ  No records older than {days} days found")


def query_by_date_range(db_path="vehicle_detection.db", hours_back=24):
    """Query data from last N hours"""
    print_separator(f"DATA FROM LAST {hours_back} HOURS")
    
    db = VehicleCountDatabase(db_path=db_path)
    
    end_time = time.time()
    start_time = end_time - (hours_back * 3600)
    
    records = db.db.get_counts_by_time_range(start_time, end_time)
    
    if not records:
        print(f"No records found from the last {hours_back} hours")
        return
    
    print(f"Found {len(records)} records\n")
    print(f"{'DateTime':<25} {'Cars':<6} {'Vans':<6} {'Motors':<7} {'Buses':<6} {'Bicycles':<8}")
    print("-" * 60)
    
    for record in records:
        print(f"{record['datetime_str']:<25} {record['cars']:<6} {record['vans']:<6} "
              f"{record['motors']:<7} {record['buses']:<6} {record['bicycles']:<8}")


def get_vehicle_totals(db_path="vehicle_detection.db"):
    """Get total vehicle counts"""
    print_separator("VEHICLE TOTALS")
    
    db = VehicleCountDatabase(db_path=db_path)
    stats = db.get_statistics()
    
    if stats['total_records'] == 0:
        print("No data in database")
        return
    
    # Calculate total time span
    latest = db.get_latest(limit=1)
    if latest:
        print(f"Data collected until: {latest[0]['datetime_str']}")
    
    print("\n TOTAL VEHICLES DETECTED:")
    print(f"  Cars:      {stats['total']['cars']:,}")
    print(f"  Vans:      {stats['total']['vans']:,}")
    print(f"  Motors:    {stats['total']['motors']:,}")
    print(f"  Buses:     {stats['total']['buses']:,}")
    print(f"  Bicycles:  {stats['total']['bicycles']:,}")
    
    total_all = (stats['total']['cars'] + stats['total']['vans'] + 
                 stats['total']['motors'] + stats['total']['buses'] + 
                 stats['total']['bicycles'])
    
    print(f"\n  TOTAL:     {total_all:,} vehicles")


def show_menu():
    """Display menu options"""
    print_separator("VEHICLE DETECTION DATABASE UTILITY")
    
    print("Options:")
    print("  1. View database info")
    print("  2. View statistics")
    print("  3. View latest records")
    print("  4. Export to CSV")
    print("  5. Backup database")
    print("  6. Query last 24 hours")
    print("  7. Get vehicle totals")
    print("  8. Clean old records (>30 days)")
    print("  9. Exit")
    print()


def main():
    """Main menu loop"""
    db_path = DEFAULT_DB_PATH
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"\n  Database not found: {db_path}")
        print("   Run your vehicle detection script first to create the database.\n")
        print(f"   Expected location: {db_path}\n")
        return
    
    while True:
        show_menu()
        choice = input("Enter your choice (1-9): ").strip()
        
        try:
            if choice == '1':
                view_database_info(db_path)
            elif choice == '2':
                view_statistics(db_path)
            elif choice == '3':
                limit = input("How many records to view? (default: 20): ").strip()
                limit = int(limit) if limit else 20
                view_latest_records(db_path, limit=limit)
            elif choice == '4':
                filename = input("Enter output filename (default: vehicle_export.csv): ").strip()
                filename = filename if filename else "vehicle_export.csv"
                export_to_csv(db_path, filename)
            elif choice == '5':
                backup_database(db_path)
            elif choice == '6':
                hours = input("Hours back to query (default: 24): ").strip()
                hours = int(hours) if hours else 24
                query_by_date_range(db_path, hours_back=hours)
            elif choice == '7':
                get_vehicle_totals(db_path)
            elif choice == '8':
                days = input("Keep records from how many days back? (default: 30): ").strip()
                days = int(days) if days else 30
                confirm = input(f"Delete records older than {days} days? (y/n): ").strip().lower()
                if confirm == 'y':
                    clean_old_records(db_path, days=days)
            elif choice == '9':
                print("\nGoodbye!\n")
                break
            else:
                print(" Invalid choice. Please try again.")
        except Exception as e:
            print(f" Error: {str(e)}")


if __name__ == "__main__":
    main()
