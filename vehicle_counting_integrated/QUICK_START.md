#  Quick Start Guide - Vehicle Counting with Database Integration

##  Integration Complete!

Your script has been modified to automatically save vehicle counts to SQLite database.

---

##  Setup Steps

### 1. Update Video Path (IMPORTANT)

Edit `scripts/InStopCounting&PassedCounting.py` and change the video path:

```python
# Line ~44
cap = cv2.VideoCapture("Videos/your_video.mp4")  # Change "Kampuchea_krom.MOV" to your video file
```

### 2. Update Model Path (if needed)

If your YOLO model is named differently:

```python
# Line ~47
model = YOLO("Version1.pt").to(device)  # Change if model name is different
```

### 3. Update Mask Image Path (Optional)

If using a different mask:

```python
# Line ~53
mask = cv2.imread("car_counting/project.png")  # or your mask path
```

---

##  How to Run

### Terminal 1: Activate Environment

```bash
cd "e:\DSE-Y3\Competition\Object Detection"
.\env\Scripts\Activate.ps1
```

### Terminal 2: Run the Script

```bash
cd vehicle_counting_integrated/scripts
python InStopCounting&PassedCounting.py
```

---

##  What Happens When Running

```
1. Video loads
2. YOLO detects vehicles frame-by-frame
3. SORT tracks objects across frames
4. Every 5 seconds: Saves current counts to SQLite database
5. On exit (press 'q'): Final counts saved to database
6. Database file created: data/vehicle_detection.db
```

### Example Output:

```
 Database module loaded successfully
 Database initialized: .../data/vehicle_detection.db
 Saved to DB - Cars: 5, Vans: 2, Motors: 3, Buses: 1, Bicycles: 0
 Saved to DB - Cars: 8, Vans: 2, Motors: 5, Buses: 1, Bicycles: 1
...
 Final counts saved to database:
   Cars: 15
   Vans: 4
   Motors: 9
   Buses: 2
   Bicycles: 1
 Video processing completed
```

---

##  Controls While Running

| Key | Action                      |
| --- | --------------------------- |
| `q` | Quit and save final counts  |
| `f` | Freeze/unfreeze video frame |

---

##  View Database Results

### Option 1: Using Database Utility

```bash
cd vehicle_counting_integrated
python database_utility.py
```

This shows:

- Total records
- Statistics (average, max, min counts)
- Export options

### Option 2: Query Directly

```bash
cd vehicle_counting_integrated
python -c "
from scripts.secure_streaming import VehicleCountDatabase
db = VehicleCountDatabase('data/vehicle_detection.db')
records = db.get_latest(limit=10)
for r in records:
    print(r)
"
```

### Option 3: View CSV Export

```bash
cd vehicle_counting_integrated
python database_utility.py  # Then select export option
```

---

##  File Structure After Running

```
vehicle_counting_integrated/
 data/
    vehicle_detection.db    ← Your database (created after first run)
 scripts/
    InStopCounting&PassedCounting.py  ← Modified with DB integration
 Videos/
    your_video.mp4          ← Your input video
 ...
```

---

##  Troubleshooting

### Issue: "Module not found"

**Solution:**

```bash
cd vehicle_counting_integrated
pip install -r requirements.txt
```

### Issue: Database not created

**Check:**

1. Ensure `data/` folder exists (created automatically)
2. Check write permissions
3. Look for error messages starting with ""

### Issue: Video not loading

**Check:**

1. Video file exists in `Videos/` folder
2. Video format is supported (mp4, mov, avi, etc.)
3. Path is relative to script location

### Issue: Model not loading

**Check:**

1. `Version1.pt` exists in root folder
2. Model name matches in code
3. CUDA drivers installed (or will use CPU)

---

##  Database Schema

The SQLite database stores:

```
Table: vehicle_counts
 id (auto-increment)
 timestamp (datetime)
 cars (integer)
 vans (integer)
 motors (integer)
 buses (integer)
 bicycles (integer)
```

Every 5 seconds while running, a new record is added with the current cumulative counts.

---

##  What The Script Does

### Main Logic:

```
For each video frame:
  1. Run YOLO detection
  2. Identify vehicle class (car, bus, truck, motorcycle, bicycle)
  3. Track with SORT algorithm (assigns ID to each vehicle)
  4. Check if vehicle is in counting area or crosses line
  5. Increment appropriate counter
  6. Every 5 seconds: Save to database
  7. Display counts on screen
```

### Vehicle Types Tracked:

-  **Car** - Standard automobiles
-  **Van** - Trucks and Tuk-tuks
-  **Motor** - Motorcycles
-  **Bus** - Buses
-  **Bicycle** - Bicycles

---

##  Next Steps

1. **Run the script** with your video
2. **View results** using `database_utility.py`
3. **Export data** to CSV for further analysis
4. **Adjust parameters** as needed (confidence threshold, counting area, etc.)

---

##  Pro Tips

- **Slow video:** Increase GPU usage by reducing frame resolution
- **Better accuracy:** Adjust confidence threshold (currently 0.3)
- **Change counting interval:** Modify `db_save_interval` in script (currently 5 seconds)
- **Custom area:** Edit `counting_area` coordinates for different regions

---

**Status:**  Ready to Use!

Start with: `python scripts/InStopCounting&PassedCounting.py`
