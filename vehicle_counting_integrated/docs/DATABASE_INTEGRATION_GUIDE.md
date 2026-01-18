# SQLite Database Integration Guide

## Overview

Your vehicle detection system has been upgraded to store data in **SQLite database** instead of `.txt` files. This provides better data management, querying, and analysis capabilities.

## Quick Start (5 minutes)

### Option 1: Database-Only (Simplest)  RECOMMENDED

1. **Open `PassedCounting.py`**

2. **Add import at the top:**

   ```python
   from secure_streaming import VehicleCountDatabase
   ```

3. **After config initialization, add:**

   ```python
   db = VehicleCountDatabase(db_path="vehicle_detection.db")
   ```

4. **Find and replace file operations in the main loop:**

   OLD:

   ```python
   output_file = open(config['output_path'], 'a')
   # ...
   output_file.write(f"Time {current_time:.1f}s: Cars: {len(totalCar)}, Vans: {len(totalVan)}, Motors: {len(totalMotor)}, Buses: {len(totalBus)}, Bicycles: {len(totalBicycle)}\n")
   output_file.flush()
   ```

   NEW:

   ```python
   vehicle_counts = {
       'cars': len(totalCar),
       'vans': len(totalVan),
       'motors': len(totalMotor),
       'buses': len(totalBus),
       'bicycles': len(totalBicycle)
   }

   if db.save_vehicle_counts(vehicle_counts):
       logger.info(f"Data saved at {current_time:.1f}s - C:{len(totalCar)}, V:{len(totalVan)}, M:{len(totalMotor)}")
   ```

5. **In the `finally` block, remove the file close and add export:**

   ```python
   # Remove: output_file.close()

   # Add this instead:
   stats = db.get_statistics()
   logger.info(f"Processing complete. Total records: {stats['total_records']}")
   db.export_csv("vehicle_detection_export.csv")
   ```

Done! Your data now saves to SQLite database.

### Option 2: Streaming + Database (Advanced)

For real-time data streaming to multiple clients with persistent storage:

```python
from secure_streaming import SecureDataStreamServer
import threading

# Initialize server
server = SecureDataStreamServer(
    db_path='vehicle_detection.db',
    api_key='your-secure-api-key'
)

# Start in background
server_thread = threading.Thread(target=server.run, daemon=True)
server_thread.start()

# In main loop:
await server.broadcast_data(vehicle_counts)  # Saves and streams
```

## Database Schema

The SQLite database automatically creates these tables:

### vehicle_counts Table

```
- id: Auto-incrementing ID
- timestamp: Unix timestamp (indexed for fast queries)
- datetime_str: Human-readable datetime (e.g., "2026-01-18 14:30:45.123")
- cars, vans, motors, buses, bicycles: Vehicle counts
- created_at: When the record was created
```

### audit_logs Table

```
- id: Auto-incrementing ID
- timestamp: Unix timestamp
- event_type: Type of event (e.g., "DATA_SAVED", "ERROR")
- message: Event description
- level: Log level (INFO, WARNING, ERROR)
- created_at: When the log was created
```

## Common Tasks

### Query Latest Data

```python
from secure_streaming import VehicleCountDatabase

db = VehicleCountDatabase(db_path="vehicle_detection.db")

# Get latest 20 records
latest = db.get_latest(limit=20)
for record in latest:
    print(f"{record['datetime_str']}: Cars={record['cars']}, Vans={record['vans']}")
```

### Get Statistics

```python
stats = db.get_statistics()

print(f"Total records: {stats['total_records']}")
print(f"Average cars per record: {stats['average']['cars']}")
print(f"Peak cars: {stats['maximum']['cars']}")
print(f"Total cars seen: {stats['total']['cars']}")
```

### Export to CSV

```python
# Export all data to CSV file
db.export_csv("vehicle_analysis.csv")

# Now open in Excel or analyze with pandas
import pandas as pd
df = pd.read_csv("vehicle_analysis.csv")
print(df.head())
print(df.describe())
```

### Time Range Query

```python
import time
from datetime import timedelta

# Get data from last hour
end_time = time.time()
start_time = end_time - 3600  # 1 hour ago

data = db.db.get_counts_by_time_range(start_time, end_time)
```

### Cleanup Old Data

```python
# Keep only last 30 days of data
deleted = db.clear_old_records(days_to_keep=30)
print(f"Deleted {deleted} old records")
```

## Database File Location

- **Default**: `vehicle_detection.db` (in current directory)
- **Custom**: Specify when creating database:
  ```python
  db = VehicleCountDatabase(db_path="/path/to/my/database.db")
  ```

## Advantages Over Text Files

| Feature            | Text File                | SQLite                      |
| ------------------ | ------------------------ | --------------------------- |
| Query speed        | Slow (parse entire file) | Fast (indexed)              |
| Data integrity     | No verification          | Built-in integrity checks   |
| Statistics         | Manual calculation       | Built-in queries            |
| Data duplication   | High                     | None                        |
| Sorting/Filtering  | Hard                     | Easy SQL                    |
| CSV export         | Manual                   | One command                 |
| Scalability        | Slow with large files    | Handles millions of records |
| Data relationships | Not possible             | Possible                    |
| Update capability  | Difficult                | Easy                        |

## Troubleshooting

### Database already locked error

- Close other connections to the database
- SQLite is file-based, so multiple processes writing simultaneously can cause this
- Solution: Don't run multiple copies of the script on the same database file

### Import error for secure_streaming

- Make sure `secure_streaming.py` is in the same directory as your script
- Or add to Python path: `import sys; sys.path.append('car_counting')`

### Database file is large

- Export old data to CSV then clear:
  ```python
  db.export_csv("archive.csv")
  db.clear_old_records(days_to_keep=7)
  ```

## Testing

Run the example script to see all features in action:

```bash
python database_integration_example.py
```

This will:

1. Show comparison between approaches
2. Create test database
3. Save sample data
4. Query and display results
5. Export to CSV
6. Show code snippets

## Migration from Text Files

If you already have data in text files:

```python
# Parse old text file and import to database
db = VehicleCountDatabase(db_path="vehicle_detection.db")

# Manually parse your text file
with open("old_vehicle_counts.txt", "r") as f:
    for line in f:
        # Parse the line and extract counts
        # Then save to database
        db.save_vehicle_counts({...})
```

## Performance

- **Insert speed**: ~1ms per record
- **Query speed**: <100ms for 100,000 records
- **Database size**: ~200 bytes per record
- **Daily records at 1Hz**: ~86,400 records = ~17MB per day

## API Reference

### VehicleCountDatabase

```python
from secure_streaming import VehicleCountDatabase

db = VehicleCountDatabase(db_path="vehicle_detection.db")

# Save data
db.save_vehicle_counts({'cars': 5, 'vans': 2, 'motors': 3, 'buses': 1, 'bicycles': 0})

# Retrieve data
latest = db.get_latest(limit=10)  # Last 10 records
stats = db.get_statistics()       # Summary statistics

# Export
db.export_csv("output.csv")       # Export to CSV

# Maintenance
total = db.get_total_records()    # Record count
deleted = db.clear_old_records(days_to_keep=30)
```

## Next Steps

1.  Update `PassedCounting.py` with database code
2.  Test with your video
3.  Query results with sample queries
4.  Export data for analysis
5.  Set up automated cleanup if needed

## Support

For detailed documentation, see docstrings in:

- `secure_streaming.py` - Main module
- `database_integration_example.py` - Working examples

Questions? Check the example scripts or docstrings!
