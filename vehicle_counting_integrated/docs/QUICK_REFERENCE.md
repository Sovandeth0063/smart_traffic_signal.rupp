# Quick Reference: SQLite Database Integration

## 3-Step Integration

### Step 1: Add Import

```python
from secure_streaming import VehicleCountDatabase
```

### Step 2: Initialize

```python
db = VehicleCountDatabase(db_path="vehicle_detection.db")
```

### Step 3: Replace File Writing

```python
# Instead of:
# output_file.write(f"Time {current_time:.1f}s: ...")

# Do this:
db.save_vehicle_counts({
    'cars': len(totalCar),
    'vans': len(totalVan),
    'motors': len(totalMotor),
    'buses': len(totalBus),
    'bicycles': len(totalBicycle)
})
```

---

## Common Operations

### Save Data

```python
db.save_vehicle_counts({'cars': 5, 'vans': 2, 'motors': 3, 'buses': 1, 'bicycles': 0})
```

### Get Latest Records

```python
latest = db.get_latest(limit=10)  # Last 10 records
for record in latest:
    print(f"{record['datetime_str']}: Cars={record['cars']}")
```

### Get Statistics

```python
stats = db.get_statistics()
print(f"Average cars: {stats['average']['cars']}")
print(f"Total cars: {stats['total']['cars']}")
```

### Export to CSV

```python
db.export_csv("results.csv")
# Open in Excel or analyze with pandas
```

### Get Total Records

```python
total = db.get_total_records()
print(f"Database has {total} records")
```

### Clean Old Data

```python
deleted = db.clear_old_records(days_to_keep=30)
print(f"Deleted {deleted} old records")
```

---

## Utilities

### View Statistics (Interactive)

```bash
python database_utility.py
```

### Test Integration

```bash
python database_integration_example.py
```

---

## Database File

- **Location**: `vehicle_detection.db` (in current directory)
- **Size**: ~200 bytes per record
- **Format**: SQLite3 (portable, no external server needed)
- **Access**: Read with any SQLite tool or Python

---

## Data Schema

```
vehicle_counts table:
 id (auto-increment)
 timestamp (indexed for fast queries)
 datetime_str (human-readable: "2026-01-18 14:30:45.123")
 cars (integer count)
 vans (integer count)
 motors (integer count)
 buses (integer count)
 bicycles (integer count)
 created_at (timestamp)
```

---

## Python API

```python
from secure_streaming import VehicleCountDatabase

db = VehicleCountDatabase(db_path="vehicle_detection.db")

# Methods:
db.save_vehicle_counts(data)           # Save data
db.get_latest(limit=10)                 # Get latest N records
db.get_statistics()                     # Get summary stats
db.export_csv(filepath)                 # Export to CSV
db.get_total_records()                  # Count records
db.clear_old_records(days_to_keep=30)  # Delete old data
```

---

## Expected Database Size

| Duration | Records   | Size   |
| -------- | --------- | ------ |
| 1 hour   | 3,600     | 720 KB |
| 1 day    | 86,400    | 17 MB  |
| 1 week   | 604,800   | 120 MB |
| 1 month  | 2,592,000 | 518 MB |

---

## Troubleshooting

| Problem          | Solution                                       |
| ---------------- | ---------------------------------------------- |
| Module not found | Ensure `secure_streaming.py` is in same folder |
| Database locked  | Close other connections to the same DB         |
| Slow queries     | Use `get_latest()` or time range filters       |
| Huge database    | Export old data, use `clear_old_records()`     |

---

## Migration from Text File

```python
# Read old text file
with open("old_data.txt") as f:
    for line in f:
        # Parse and extract counts
        db.save_vehicle_counts({...})
```

---

## Advanced: Query by Time Range

```python
import time

# Get data from last hour
end = time.time()
start = end - 3600

data = db.db.get_counts_by_time_range(start, end)
```

---

## File Structure

```
Object Detection/
 car_counting/
    PassedCounting.py           (← Update this)
    secure_streaming.py         (← New: Database module)
    database_integration_example.py  (← Examples)
    sort.py
 database_utility.py             (← Data management tool)
 DATABASE_INTEGRATION_GUIDE.md   (← Full documentation)
```

---

## Need Help?

1. Read: `DATABASE_INTEGRATION_GUIDE.md`
2. Run: `python database_integration_example.py`
3. Manage: `python database_utility.py`
4. Check: Docstrings in `secure_streaming.py`

---

## Key Advantages

 No more parsing text files  
 Fast queries with indexing  
 Built-in statistics  
 Easy CSV export  
 Handles millions of records  
 No external server needed  
 Time-range filtering  
 Data integrity checks

---

**Created**: January 18, 2026  
**Version**: 1.0  
**Database**: SQLite3
