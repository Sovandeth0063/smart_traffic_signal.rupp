"""
PRACTICAL EXAMPLE: Using SQLite Database with PassedCounting.py
================================================================

This script demonstrates how to integrate SQLite database storage
with your existing PassedCounting.py vehicle detection system.

Two approaches are shown:
1. Database-only: Simple replacement for text file storage
2. Streaming + Database: Secure streaming with persistent storage

Run this script to understand the integration patterns.
"""

import time
from secure_streaming import VehicleCountDatabase, SecureDataStreamServer
import threading
import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== APPROACH 1: DATABASE-ONLY (SIMPLEST) ====================
def example_database_only():
    """
    Simplest approach: Replace text file with SQLite database
    
    This is what you should add to PassedCounting.py main loop:
    """
    print("\n" + "="*60)
    print("APPROACH 1: DATABASE-ONLY STORAGE (RECOMMENDED FOR SIMPLICITY)")
    print("="*60)
    
    # Initialize database
    db = VehicleCountDatabase(db_path="example_vehicle_detection.db")
    
    # Simulate vehicle detection data over time
    print("\n1. Simulating vehicle detection with periodic data saves...")
    
    for i in range(5):
        # Simulated vehicle counts (in real code, these come from YOLO)
        vehicle_counts = {
            'cars': 5 + i,
            'vans': 2 + (i % 2),
            'motors': 3 + i,
            'buses': 1,
            'bicycles': i
        }
        
        # Save to database (replaces: output_file.write(...))
        success = db.save_vehicle_counts(vehicle_counts)
        if success:
            print(f"   [{i+1}] Saved: Cars={vehicle_counts['cars']}, Vans={vehicle_counts['vans']}, Motors={vehicle_counts['motors']}")
        
        time.sleep(0.5)
    
    # Query and display data
    print("\n2. Retrieving latest records from database...")
    latest = db.get_latest(limit=5)
    for record in latest:
        print(f"   {record['datetime_str']}: C={record['cars']}, V={record['vans']}, M={record['motors']}, B={record['buses']}, Bi={record['bicycles']}")
    
    # Get statistics
    print("\n3. Database Statistics:")
    stats = db.get_statistics()
    print(f"   Total records: {stats['total_records']}")
    print(f"   Average cars: {stats['average']['cars']:.1f}")
    print(f"   Max buses: {stats['maximum']['buses']}")
    print(f"   Total motors detected: {stats['total']['motors']}")
    
    # Export to CSV
    print("\n4. Exporting to CSV...")
    csv_file = "vehicle_counts_example.csv"
    if db.export_csv(csv_file):
        print(f"    Data exported to: {csv_file}")
    
    print("\n Approach 1 completed successfully!\n")


# ==================== APPROACH 2: STREAMING + DATABASE ====================
def example_streaming_with_database():
    """
    Advanced approach: Secure streaming + database storage
    
    Use this if you want to:
    - Stream real-time data to multiple clients
    - Permanently store data in database
    - Have secure authentication
    """
    print("\n" + "="*60)
    print("APPROACH 2: SECURE STREAMING + DATABASE STORAGE")
    print("="*60)
    
    # Initialize server with database
    server = SecureDataStreamServer(
        host='127.0.0.1',
        port=8443,
        api_key='your-secure-api-key',
        db_path='example_streaming_vehicle_detection.db',
        rate_limit=100
    )
    
    print("\n1. Server initialized (database: example_streaming_vehicle_detection.db)")
    print(f"   Listen on: wss://127.0.0.1:8443")
    
    # In real usage, start server in background:
    # server_thread = threading.Thread(target=server.run, daemon=True)
    # server_thread.start()
    # print("    Server started in background")
    
    # Simulate broadcasting vehicle data
    print("\n2. Simulating vehicle data broadcast...")
    
    async def broadcast_simulation():
        for i in range(5):
            vehicle_counts = {
                'cars': 5 + i,
                'vans': 2 + (i % 2),
                'motors': 3 + i,
                'buses': 1,
                'bicycles': i
            }
            
            # Broadcast to clients and save to database
            await server.broadcast_data(vehicle_counts)
            print(f"   [{i+1}] Broadcasted and saved to database")
            await asyncio.sleep(0.5)
    
    # Run simulation
    asyncio.run(broadcast_simulation())
    
    # Get stored data
    print("\n3. Retrieving stored data from server database...")
    stored_records = server.get_latest_vehicle_counts(limit=5)
    for record in stored_records:
        print(f"   {record['datetime_str']}: C={record['cars']}, V={record['vans']}, M={record['motors']}")
    
    # Get statistics
    print("\n4. Server Database Statistics:")
    stats = server.get_database_statistics()
    print(f"   Total records stored: {server.get_total_stored_records()}")
    print(f"   Average vehicles per record: {stats['average']['cars'] + stats['average']['vans']:.1f}")
    
    print("\n Approach 2 completed successfully!\n")


# ==================== INTEGRATION CODE SNIPPETS ====================
def show_integration_snippets():
    """
    Show exact code to add to PassedCounting.py
    """
    print("\n" + "="*60)
    print("CODE SNIPPETS TO ADD TO PassedCounting.py")
    print("="*60)
    
    print("\n1. IMPORTS (Add at top of file):")
    print("""
    from secure_streaming import VehicleCountDatabase
    """)
    
    print("\n2. INITIALIZATION (Add after config setup):")
    print("""
    # Initialize SQLite database
    db = VehicleCountDatabase(db_path="vehicle_detection.db")
    """)
    
    print("\n3. REPLACE FILE OPERATIONS (In main processing loop):")
    print("""
    # OLD CODE (Remove this):
    # output_file = open(config['output_path'], 'a')
    # ...
    # output_file.write(f"Time {current_time:.1f}s: ...")
    # output_file.flush()
    
    # NEW CODE (Replace with this):
    vehicle_counts = {
        'cars': len(totalCar),
        'vans': len(totalVan),
        'motors': len(totalMotor),
        'buses': len(totalBus),
        'bicycles': len(totalBicycle)
    }
    
    if db.save_vehicle_counts(vehicle_counts):
        logger.info(f"Data saved - C:{len(totalCar)}, V:{len(totalVan)}, M:{len(totalMotor)}")
    """)
    
    print("\n4. CLEANUP (Replace in finally block):")
    print("""
    # OLD CODE (Remove this):
    # if 'output_file' in locals():
    #     output_file.close()
    
    # NEW CODE (Replace with this):
    # Database doesn't need explicit close (connection is managed)
    # Export final data if needed:
    stats = db.get_statistics()
    logger.info(f"Processing complete. Total records: {stats['total_records']}")
    db.export_csv("vehicle_detection_export.csv")
    """)
    
    print("\n5. QUERY DATA AFTER PROCESSING:")
    print("""
    # View latest records
    latest = db.get_latest(limit=10)
    
    # View statistics
    stats = db.get_statistics()
    print(f"Total cars: {stats['total']['cars']}")
    
    # Export to CSV for analysis
    db.export_csv("results.csv")
    """)


# ==================== DATABASE COMPARISON ====================
def show_comparison():
    """
    Show comparison between text file and database approaches
    """
    print("\n" + "="*60)
    print("TEXT FILE vs SQLite DATABASE COMPARISON")
    print("="*60)
    
    print("\n TEXT FILE APPROACH (Current):")
    print("   Pros:  Simple, easy to understand")
    print("   Cons:  Hard to query, parse, or analyze")
    print("          Data duplication")
    print("          No indexing")
    print("          Difficult to filter by time")
    print("          No built-in statistics")
    
    print("\n  SQLite DATABASE APPROACH (Recommended):")
    print("   Pros:  Structured data storage")
    print("          Fast querying and filtering")
    print("          Automatic indexing")
    print("          Built-in statistics")
    print("          Easy CSV export")
    print("          Supports millions of records")
    print("          No external server needed")
    print("   Cons:  Slightly more setup")
    print("          Need to learn SQL (optional)")


# ==================== MAIN ====================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("SQLITE DATABASE INTEGRATION EXAMPLES")
    print("="*60)
    
    # Show comparison
    show_comparison()
    
    # Run examples
    try:
        example_database_only()
        example_streaming_with_database()
    except Exception as e:
        logger.error(f"Error running examples: {str(e)}")
    
    # Show code snippets
    show_integration_snippets()
    
    print("\n" + "="*60)
    print(" All examples completed!")
    print("="*60)
    print("\nNext steps:")
    print("1. Choose your preferred approach (database-only is simpler)")
    print("2. Copy the integration code snippets to PassedCounting.py")
    print("3. Replace file operations with database operations")
    print("4. Test with your video")
    print("5. Query and export data as needed")
    print("\nFor help, check the docstrings in secure_streaming.py\n")
