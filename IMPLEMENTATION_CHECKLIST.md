# SQLite Database Integration Checklist

## Pre-Implementation

- [ ] Read `DATABASE_INTEGRATION_GUIDE.md`
- [ ] Review `QUICK_REFERENCE.md`
- [ ] Run `python database_integration_example.py` to see examples
- [ ] Backup your current `PassedCounting.py`

## Step 1: Update Imports (5 minutes)

In `PassedCounting.py`, add at the top with other imports:

```python
from secure_streaming import VehicleCountDatabase
```

- [ ] Import added
- [ ] File saves without errors

## Step 2: Initialize Database (5 minutes)

After the config is set up in `main()`, add:

```python
# Initialize SQLite database for vehicle counts
db = VehicleCountDatabase(db_path="vehicle_detection.db")
```

- [ ] Database initialization added
- [ ] Placed after config setup

## Step 3: Replace File Opening (5 minutes)

REMOVE these lines:

```python
output_file = open(config['output_path'], 'a')
```

- [ ] Old file opening code removed

## Step 4: Replace File Writing (10 minutes)

In the main loop, find this section:

```python
if current_time - last_write_time >= interval:
    output_file.write(f"Time {current_time:.1f}s: Cars: ...")
    output_file.flush()
```

REPLACE with:

```python
if current_time - last_write_time >= interval:
    vehicle_counts = {
        'cars': len(totalCar),
        'vans': len(totalVan),
        'motors': len(totalMotor),
        'buses': len(totalBus),
        'bicycles': len(totalBicycle)
    }

    if db.save_vehicle_counts(vehicle_counts):
        logger.info(f"Data saved at {current_time:.1f}s - C:{len(totalCar)}, V:{len(totalVan)}, M:{len(totalMotor)}, B:{len(totalBus)}, Bi:{len(totalBicycle)}")

    last_write_time = current_time
```

- [ ] Old file writing code removed
- [ ] Database saving code added
- [ ] Logger call updated

## Step 5: Replace Cleanup Code (5 minutes)

In the `finally` block, REMOVE:

```python
if 'output_file' in locals():
    output_file.close()
```

REPLACE with:

```python
# Export data and show final statistics
try:
    stats = db.get_statistics()
    logger.info(f"Processing complete. Total records: {stats['total_records']}")
    db.export_csv("vehicle_detection_export.csv")
    logger.info("Data exported to: vehicle_detection_export.csv")
except Exception as e:
    logger.error(f"Error during export: {str(e)}")
```

- [ ] Old file close code removed
- [ ] Statistics logging added
- [ ] CSV export added

## Step 6: Test Integration (15 minutes)

Run your updated `PassedCounting.py`:

```bash
python car_counting/PassedCounting.py
```

- [ ] Script starts without errors
- [ ] `vehicle_detection.db` file is created
- [ ] Vehicle counts are displayed on screen
- [ ] No file opening/writing error messages

## Step 7: Verify Database (5 minutes)

Run the database utility:

```bash
python database_utility.py
```

Then select option 1 (View database info):

- [ ] Database file shows in utility
- [ ] Records are listed
- [ ] Total record count is correct

## Step 8: Export and Review (5 minutes)

In database utility, select option 4 (Export to CSV):

- [ ] CSV file is created
- [ ] File contains your data
- [ ] Can be opened in Excel/Sheets

## Step 9: Test Statistics (5 minutes)

In database utility, select option 2 (View statistics):

- [ ] Statistics show correct totals
- [ ] Average values are calculated
- [ ] Minimum/maximum values are shown

## Post-Implementation

### Cleanup Old Configuration

- [ ] Remove old `.txt` output file if no longer needed
- [ ] Verify all features work with new database

### Documentation

- [ ] Note the database location: `vehicle_detection.db`
- [ ] Save CSV exports for long-term storage
- [ ] Set up regular backups if needed

### Optional Enhancements

- [ ] Add database backup script to cron/scheduler
- [ ] Set up automatic old record cleanup (`clear_old_records`)
- [ ] Configure automatic CSV exports
- [ ] Set up data analysis scripts

## Verification Checklist

Before declaring complete, verify:

- [ ] Vehicle detection works as before
- [ ] No performance degradation
- [ ] Database file created automatically
- [ ] Data saves on each interval
- [ ] Latest records retrievable
- [ ] Statistics calculated correctly
- [ ] CSV export works
- [ ] No error messages in logs

## Rollback Plan (If Needed)

If you need to revert:

1. [ ] Restore backup of `PassedCounting.py`
2. [ ] Delete `vehicle_detection.db` file
3. [ ] Delete `vehicle_detection_export.csv` file
4. [ ] Run original PassedCounting.py

## Common Issues & Fixes

### Issue: "Module not found: secure_streaming"

**Fix**: Ensure `secure_streaming.py` is in same directory as your script

### Issue: Database locked error

**Fix**: Close any other connections to the database file

### Issue: Old data not showing

**Fix**: Make sure you're pointing to correct database path

### Issue: CSV file is empty

**Fix**: Ensure data has been saved first (run detection script)

## Time Estimate

- Pre-check: 10 minutes
- Integration: 30 minutes
- Testing: 15 minutes
- **Total: ~1 hour**

## Success Criteria

✅ Vehicle detection runs without errors  
✅ Data saves to SQLite database  
✅ Database can be queried  
✅ CSV export works  
✅ Statistics are calculated  
✅ No more text file writing

## After Integration

You can now:

```python
from secure_streaming import VehicleCountDatabase

db = VehicleCountDatabase()

# Query data
latest = db.get_latest(limit=50)

# Get statistics
stats = db.get_statistics()

# Export for analysis
db.export_csv("my_analysis.csv")

# Import into pandas
import pandas as pd
df = pd.read_csv("my_analysis.csv")
df.describe()
```

## Questions?

1. Check: `DATABASE_INTEGRATION_GUIDE.md` - Full documentation
2. Check: `QUICK_REFERENCE.md` - Quick lookup
3. Run: `python database_integration_example.py` - See working examples
4. Check: Docstrings in `secure_streaming.py` - API details

## Sign-Off

- [ ] Implementation complete
- [ ] All tests passed
- [ ] Documentation reviewed
- [ ] Database working correctly
- [ ] Ready for production use

---

**Status**: Ready to implement
**Created**: January 18, 2026
**Estimated Time**: 1 hour
**Difficulty**: Easy ⭐
