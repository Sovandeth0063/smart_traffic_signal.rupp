#  Vehicle Counting Implementation Guide

## Complete Flow: YOLO → Vehicle Type Counting → SQLite Database

---

##  PURPOSE ALIGNMENT CHECK

Your Goal: Use pretrained YOLO to count vehicle TYPES from video and save to SQLite database

| Requirement           | Status     | File                                                    |
| --------------------- | ---------- | ------------------------------------------------------- |
| Pretrained YOLO model |  Yes     | Uses `Version1.pt`                                      |
| Count vehicle TYPES   |  Yes     | Counts: car, bus, truck, tuk-tuk, motorcycle, bicycle   |
| Process VIDEO input   |  Yes     | Uses `cv2.VideoCapture()`                               |
| Save to SQLite        |  PARTIAL | Database setup exists but NOT integrated into main flow |

** ISSUE**: The vehicle counting scripts do NOT currently save to the database. You need to integrate them!

---

##  Complete Data Flow (What Should Happen)

```
VIDEO INPUT (your_video.mp4)
    ↓
YOLO Detection (Version1.pt)
    ↓
SORT Tracking (Tracks vehicle across frames)
    ↓
Count by Vehicle Type:
  - Cars
  - Buses
  - Trucks/Vans
  - Motorcycles
  - Bicycles
    ↓
Save to SQLite Database ← (MISSING INTEGRATION)
    ↓
OUTPUT: vehicle_detection.db with all records
```

---

##  HOW TO RUN & What Each File Does

### 1. **InStopCounting&PassedCounting.py**  BEST FOR YOUR PURPOSE

**What it does:**

-  Loads your pretrained YOLO model (`Version1.pt`)
-  Reads video from `Videos/Kampuchea_krom.MOV`
-  Detects vehicles with SORT tracking
-  Counts by TYPE in two modes:
  - Area counting (vehicles in a specific region)
  - Line crossing counting (vehicles crossing a line)
-  **Problem**: Only saves to TEXT file, NOT database!

**How to run:**

```bash
cd vehicle_counting_integrated/scripts
python InStopCounting&PassedCounting.py
```

**Logic Explanation:**

```
1. Load video frame by frame
2. Run YOLO detection on each frame
3. Use SORT tracker to track objects across frames (same vehicle = same ID)
4. For each tracked object:
   - Identify vehicle type using class name
   - Check if it's in counting area → increment area counter
   - Check if it crosses the line → add to cumulative line counter
5. Display counts on screen
6. Save to text file (vehicle_countsversion2.txt)
```

---

### 2. **PassedCounting.py** (More Advanced)

**What it does:**

- Similar to above BUT with MORE security features:
  - File validation
  - Configuration validation
  - Security logging
  - Input sanitization
- Also saves to TEXT only

**How to run:**

```bash
cd vehicle_counting_integrated/scripts
python PassedCounting.py
```

---

### 3. **secure_streaming.py** (Database Integration)

**What it does:**

-  Contains the `VehicleCountDatabase` class
-  Handles SQLite database operations
-  Provides encryption & authentication for data streaming
-  Can save vehicle counts to database

**Key Functions:**

```python
db = VehicleCountDatabase(db_path="vehicle_detection.db")
db.save_vehicle_counts({'cars': 5, 'vans': 2, 'motors': 3, 'buses': 1})
db.get_latest(limit=10)
db.get_statistics()
db.export_csv("export.csv")
```

---

### 4. **database_integration_example.py** (Template Example)

**What it does:**

- Shows how to USE the database in your counting script
- Demonstrates the integration pattern
- Provides copy-paste code examples

**Key Example:**

```python
from secure_streaming import VehicleCountDatabase

db = VehicleCountDatabase(db_path="vehicle_detection.db")
vehicle_counts = {'cars': 5, 'vans': 2, 'motors': 3, 'buses': 1}
db.save_vehicle_counts(vehicle_counts)
```

---

### 5. **database_utility.py** (Database Management)

**What it does:**

- View database statistics
- Export data to CSV
- Query by date range
- View/manage records

**How to use:**

```bash
python database_utility.py
```

---

##  CURRENT GAP - WHAT'S MISSING

Your scripts count vehicles correctly BUT **don't save to database**!

Currently they save to TEXT file:

```
vehicle_countsversion2.txt  ← TEXT FILE (basic)
```

Should save to DATABASE:

```
vehicle_detection.db  ← SQLITE DATABASE (better for analysis)
```

---

##  SOLUTION: Integrate Database Saving

To make it work exactly as you want, you need to add database integration to `InStopCounting&PassedCounting.py`.

**Add these lines at the top:**

```python
from secure_streaming import VehicleCountDatabase
db = VehicleCountDatabase(db_path="vehicle_detection.db")
```

**Add this in the main loop (after counting frame data):**

```python
# After you have: cars_in_area, vans_in_area, motors_in_area, bus_in_area, bicycles_in_area
vehicle_counts = {
    'cars': len(totalCar_line),
    'vans': len(totalVan_line),
    'motors': len(totalMotor_line),
    'buses': len(totalBus_line),
    'bicycles': len(totalBicycle_line)
}
db.save_vehicle_counts(vehicle_counts)
```

---

##  STEP-BY-STEP TO RUN NOW

### Step 1: Prepare Your Video

```bash
# Place your video file in:
vehicle_counting_integrated/Videos/your_video.mp4
```

### Step 2: Update Video Path

Edit `InStopCounting&PassedCounting.py` line that loads video:

```python
cap = cv2.VideoCapture("Videos/your_video.mp4")  # Change file name
```

### Step 3: Run Current Version (Counts Only)

```bash
cd vehicle_counting_integrated/scripts
python InStopCounting&PassedCounting.py
```

Output: Text file with counts

### Step 4: To Add Database Integration

I can modify the script for you to save directly to SQLite.

---

##  Vehicle Types Detected

Your YOLO model detects:

```
- car          (Class 2)
- bus          (Class 5)
- truck        (Class 7)
- motorcycle   (Class 3)
- bicycle      (Class 1)
- tuk-tuk      (Class 5)
```

Each is counted separately and can be queried from the database.

---

##  Summary: What Works vs What Doesn't

| Feature                  | Status            | Fix                       |
| ------------------------ | ----------------- | ------------------------- |
| YOLO Detection           |  Working        | None needed               |
| Vehicle Type Recognition |  Working        | None needed               |
| Video Processing         |  Working        | None needed               |
| Frame-by-frame Tracking  |  Working        | None needed               |
| Counting Logic           |  Working        | None needed               |
| Save to Database         |  NOT Integrated | See "SOLUTION" above      |
| Query Database           |  Available      | Use `database_utility.py` |

---

##  NEXT STEPS

**Option A: Use current version (saves to text)**

1. Run script as-is
2. Results in `vehicle_countsversion2.txt`

**Option B: Add database integration (RECOMMENDED)**

1. I can modify the script to save to SQLite
2. Results in `vehicle_detection.db`
3. Query with `database_utility.py`

Would you like me to **add database integration to the main script**?
