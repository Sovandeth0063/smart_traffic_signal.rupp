"""
Export Database to traffic_data.txt

This script bridges the detection system (SQLite database) with the simulation system.
It reads the latest vehicle counts from the database and exports them to traffic_data.txt
in the format expected by the simulation scripts.

Usage:
    python export_db_to_traffic_data.py

The script will:
1. Connect to vehicle_detection.db
2. Get the latest vehicle counts
3. Write to traffic_data.txt in the required format
"""

import sqlite3
import os
import sys

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PROJECT_ROOT, "data", "vehicle_detection.db")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "traffic_data.txt")


def get_latest_counts_from_db():
    """Read the latest vehicle counts from the SQLite database."""
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database not found: {DB_PATH}")
        print("   Run PassedCounting.py first to generate detection data.")
        return None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get the latest record
        cursor.execute("""
            SELECT cars, vans, motors, buses, bicycles, datetime_str
            FROM vehicle_counts
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'cars': row[0],
                'vans': row[1],      # trucks in simulation
                'motors': row[2],    # motorcycles/bikes in simulation
                'buses': row[3],     # tuk-tuks in simulation
                'bicycles': row[4],
                'timestamp': row[5]
            }
        else:
            print("[ERROR] No data found in database.")
            return None
            
    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        return None


def get_statistics_from_db():
    """Get average counts for more representative data."""
    if not os.path.exists(DB_PATH):
        return None
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get average counts (more representative than single record)
        cursor.execute("""
            SELECT 
                ROUND(AVG(cars)) as avg_cars,
                ROUND(AVG(vans)) as avg_vans,
                ROUND(AVG(motors)) as avg_motors,
                ROUND(AVG(buses)) as avg_buses,
                ROUND(AVG(bicycles)) as avg_bicycles,
                COUNT(*) as total_records
            FROM vehicle_counts
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[5] > 0:  # Check if there are records
            return {
                'cars': int(row[0] or 0),
                'vans': int(row[1] or 0),
                'motors': int(row[2] or 0),
                'buses': int(row[3] or 0),
                'bicycles': int(row[4] or 0),
                'total_records': row[5]
            }
        return None
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None


def export_to_traffic_data(counts, use_phases=True):
    """
    Export counts to traffic_data.txt in the simulation format.
    
    Format (8 lines):
        Line 1: Phase 0 Cars
        Line 2: Phase 0 Motorcycles (motors)
        Line 3: Phase 0 Trucks (vans)
        Line 4: Phase 0 Tuk-tuks (buses)
        Line 5: Phase 1 Cars
        Line 6: Phase 1 Motorcycles
        Line 7: Phase 1 Trucks
        Line 8: Phase 1 Tuk-tuks
    
    Mapping from database to simulation:
        - cars → Cars
        - motors → Motorcycles/Bikes
        - vans → Trucks
        - buses → Tuk-tuks/Buses
    """
    
    if use_phases:
        # Split counts between two phases (simulating two directions)
        # Phase 0: ~40% of traffic, Phase 1: ~60% of traffic
        p0_cars = max(1, int(counts['cars'] * 0.4))
        p0_motos = max(1, int(counts['motors'] * 0.4))
        p0_trucks = int(counts['vans'] * 0.4)
        p0_tuktuks = int(counts['buses'] * 0.4)
        
        p1_cars = counts['cars'] - p0_cars
        p1_motos = counts['motors'] - p0_motos
        p1_trucks = counts['vans'] - p0_trucks
        p1_tuktuks = counts['buses'] - p0_tuktuks
    else:
        # All traffic in Phase 1 (simpler approach)
        p0_cars, p0_motos, p0_trucks, p0_tuktuks = 0, 0, 0, 0
        p1_cars = counts['cars']
        p1_motos = counts['motors']
        p1_trucks = counts['vans']
        p1_tuktuks = counts['buses']
    
    # Write to file
    try:
        with open(OUTPUT_PATH, 'w') as f:
            f.write(f"{p0_cars}\n")
            f.write(f"{p0_motos}\n")
            f.write(f"{p0_trucks}\n")
            f.write(f"{p0_tuktuks}\n")
            f.write(f"{p1_cars}\n")
            f.write(f"{p1_motos}\n")
            f.write(f"{p1_trucks}\n")
            f.write(f"{p1_tuktuks}\n")
        
        print(f"[OK] Exported to: {OUTPUT_PATH}")
        print(f"\n[DATA] Traffic Data Written:")
        print(f"   Phase 0: Cars={p0_cars}, Motos={p0_motos}, Trucks={p0_trucks}, Tuk-tuks={p0_tuktuks}")
        print(f"   Phase 1: Cars={p1_cars}, Motos={p1_motos}, Trucks={p1_trucks}, Tuk-tuks={p1_tuktuks}")
        print(f"\n   Total Spawn Limits:")
        print(f"   - Cars: {p0_cars + p1_cars}")
        print(f"   - Bikes/Motos: {p0_motos + p1_motos}")
        print(f"   - Trucks: {p0_trucks + p1_trucks}")
        print(f"   - Buses/Tuk-tuks: {p0_tuktuks + p1_tuktuks}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error writing file: {e}")
        return False


def main():
    print("=" * 50)
    print("  Database → traffic_data.txt Exporter")
    print("=" * 50)
    print(f"\n[PATH] Database: {DB_PATH}")
    print(f"[PATH] Output: {OUTPUT_PATH}\n")
    
    # Try to get statistics (average) first for more representative data
    print("[INFO] Reading from database...")
    stats = get_statistics_from_db()
    
    if stats:
        print(f"\n[OK] Found {stats['total_records']} records in database")
        print(f"\n[STATS] Average Counts:")
        print(f"   Cars: {stats['cars']}")
        print(f"   Vans/Trucks: {stats['vans']}")
        print(f"   Motorcycles: {stats['motors']}")
        print(f"   Buses/Tuk-tuks: {stats['buses']}")
        print(f"   Bicycles: {stats['bicycles']} (not used in simulation)")
        
        # Also show latest record
        latest = get_latest_counts_from_db()
        if latest:
            print(f"\n[LATEST] Latest Record ({latest['timestamp']}):")
            print(f"   Cars: {latest['cars']}, Vans: {latest['vans']}, Motors: {latest['motors']}, Buses: {latest['buses']}")
        
        # Ask user which data to use
        print("\n" + "-" * 50)
        print("Choose data source:")
        print("  1. Use LATEST record")
        print("  2. Use AVERAGE counts")
        print("  3. Cancel")
        
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        if choice == '1':
            if latest:
                export_to_traffic_data(latest)
            else:
                print("[ERROR] No latest record available")
        elif choice == '2':
            export_to_traffic_data(stats)
        else:
            print("[CANCELLED] Cancelled")
            return
            
    else:
        # Fallback to latest counts only
        latest = get_latest_counts_from_db()
        if latest:
            print(f"\n[OK] Latest Record ({latest['timestamp']}):")
            print(f"   Cars: {latest['cars']}")
            print(f"   Vans/Trucks: {latest['vans']}")
            print(f"   Motorcycles: {latest['motors']}")
            print(f"   Buses/Tuk-tuks: {latest['buses']}")
            
            confirm = input("\nExport this data? (y/n): ").strip().lower()
            if confirm == 'y':
                export_to_traffic_data(latest)
            else:
                print("[CANCELLED] Cancelled")
        else:
            print("\n[ERROR] No data available in database.")
            print("   Run PassedCounting.py first to generate detection data.")
    
    print("\n" + "=" * 50)
    print("Done! You can now run the simulation:")
    print("  python smart-simulation.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
