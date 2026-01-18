#  Vehicle Counting Integration - Complete Package

This folder contains all files needed for vehicle counting with YOLO detection and database recording.

##  Folder Structure

```
vehicle_counting_integrated/
 scripts/                          # All Python scripts
    yolo_webcam.py               # Real-time vehicle detection from webcam
    yolo_pic.py                  # Vehicle detection from images
    Car_counting_test.py          # Testing script for vehicle counting
    PassedCounting.py             # Count vehicles passing a line
    InStopCounting&PassedCounting.py  # Combined counting logic
    database_integration_example.py   # Database integration template
    secure_streaming.py           # Secure streaming implementation
    sort.py                       # SORT tracking algorithm

 data/                             # Data and logs
    vehicle_counts.txt            # Vehicle count records
    vehicle_countsversion2.txt    # Updated vehicle count records
    (other generated data files)

 docs/                             # Documentation
    DATABASE_INTEGRATION_GUIDE.md # Complete integration guide
    README_DATABASE.md            # Database overview
    QUICK_REFERENCE.md            # Quick setup guide
    security_note.md              # Security considerations

 database_utility.py               # Database utility functions
 requirements.txt                  # Python dependencies
 README.md                          # This file

```

##  Quick Start

### 1. Install Dependencies

```bash
cd vehicle_counting_integrated
pip install -r requirements.txt
```

### 2. Run Vehicle Counting with Webcam

```bash
python scripts/yolo_webcam.py
```

### 3. Run Vehicle Counting from Image

```bash
python scripts/yolo_pic.py
```

### 4. Test Database Integration

```bash
python scripts/Car_counting_test.py
```

##  Key Components

| File                              | Purpose                                                            |
| --------------------------------- | ------------------------------------------------------------------ |
| `yolo_webcam.py`                  | Real-time detection from webcam, counts vehicles, logs to database |
| `database_utility.py`             | Handles all database operations and connections                    |
| `database_integration_example.py` | Shows how to integrate database with detection                     |
| `sort.py`                         | SORT algorithm for tracking multiple vehicles                      |
| `PassedCounting.py`               | Counts vehicles that pass a specific line                          |

##  Database Integration

The system uses SQLite to store vehicle counts. Key operations:

- **Record Vehicle Counts**: Automatically stores detection results
- **Query Historical Data**: Retrieve past counts and analytics
- **Generate Reports**: Analysis of vehicle movement patterns

See [DATABASE_INTEGRATION_GUIDE.md](docs/DATABASE_INTEGRATION_GUIDE.md) for detailed instructions.

##  Documentation

- **Start with**: [README_DATABASE.md](docs/README_DATABASE.md) - 5-minute overview
- **Quick reference**: [QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - Common operations
- **Full guide**: [DATABASE_INTEGRATION_GUIDE.md](docs/DATABASE_INTEGRATION_GUIDE.md) - Complete details

##  Configuration

Edit the scripts to customize:

- Detection confidence thresholds
- Database location and name
- Video source (webcam ID, file path)
- Output logging preferences

##  Data Files

All vehicle count data is stored in the `data/` folder:

- `vehicle_counts.txt` - Main count log
- `vehicle_countsversion2.txt` - Updated format counts

##  Troubleshooting

1. **Webcam not detected**: Check camera connection and permissions
2. **Database errors**: Verify `database_utility.py` is in the same folder
3. **Import errors**: Ensure all packages from `requirements.txt` are installed
4. **Low detection accuracy**: Adjust confidence thresholds in YOLO config

##  Next Steps

1. Review [README_DATABASE.md](docs/README_DATABASE.md)
2. Run `Car_counting_test.py` to verify setup
3. Start with `yolo_pic.py` on test images
4. Move to `yolo_webcam.py` for real-time counting
5. Check `data/vehicle_counts.txt` for results

##  Verification

To verify everything is working:

```bash
python scripts/Car_counting_test.py
```

This will test:

- Database connectivity
- File permissions
- Required packages
- Data logging functionality

---

**Created**: January 18, 2026  
**Version**: 1.0 - Complete Integration Package
