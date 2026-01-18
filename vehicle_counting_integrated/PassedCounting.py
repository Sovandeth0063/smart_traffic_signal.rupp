import torch
import numpy as np
from ultralytics import YOLO
import cv2
import cvzone
import math
from sort import Sort
import time
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Import database utility
try:
    from secure_streaming import VehicleCountDatabase
    print(" Database module loaded successfully")
except ImportError as e:
    print(f" Warning: Could not import database module: {e}")
    print("   Vehicle counts will be saved to TEXT file only")
    VehicleCountDatabase = None

# Configure logging for security auditing
logging.basicConfig(
    filename='vehicle_detection.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_file_exists(file_path):
    """Validate that required files exist before processing"""
    if not os.path.isfile(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Required file not found: {file_path}")
    return True

def validate_video_source(video_path):
    """Validate video source before loading"""
    try:
        validate_file_exists(video_path)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            raise ValueError(f"Cannot open video file: {video_path}")
        cap.release()
        logger.info(f"Video validated successfully: {video_path}")
        return True
    except Exception as e:
        logger.error(f"Video validation error: {str(e)}")
        raise

def validate_model_file(model_path):
    """Validate YOLO model file"""
    try:
        validate_file_exists(model_path)
        logger.info(f"Model file validated: {model_path}")
        return True
    except Exception as e:
        logger.error(f"Model validation error: {str(e)}")
        raise

def sanitize_output_path(output_path):
    """Sanitize and validate output file path"""
    try:
        path = Path(output_path)
        # Prevent directory traversal attacks
        if ".." in str(path):
            logger.warning(f"Attempted directory traversal in output path: {output_path}")
            raise ValueError("Invalid output path: directory traversal detected")
        
        # Ensure the output directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output path validated: {output_path}")
        return str(path)
    except Exception as e:
        logger.error(f"Output path validation error: {str(e)}")
        raise

def calculate_iou(box1, box2):
    """Calculate Intersection over Union with input validation"""
    try:
        if len(box1) != 4 or len(box2) != 4:
            logger.warning("Invalid box dimensions for IoU calculation")
            return 0
        
        x1, y1, x2, y2 = box1
        x1_g, y1_g, x2_g, y2_g = box2

        xi1 = max(x1, x1_g)
        yi1 = max(y1, y1_g)
        xi2 = min(x2, x2_g)
        yi2 = min(y2, y2_g)
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)

        box1_area = (x2 - x1) * (y2 - y1)
        box2_area = (x2_g - x1_g) * (y2_g - y1_g)
        union_area = box1_area + box2_area - inter_area

        if union_area == 0:
            return 0
        
        return inter_area / union_area
    except Exception as e:
        logger.error(f"IoU calculation error: {str(e)}")
        return 0

def validate_config(config):
    """Validate configuration parameters"""
    try:
        assert config['interval'] > 0, "Interval must be positive"
        assert config['confidence_threshold'] > 0 and config['confidence_threshold'] <= 1, "Confidence must be between 0 and 1"
        assert all(isinstance(v, int) for v in config['limits']), "Limits must be integers"
        logger.info("Configuration validated successfully")
        return True
    except AssertionError as e:
        logger.error(f"Configuration validation error: {str(e)}")
        raise

def main():
    try:
        # Configuration with validation
        config = {
            'video_path': "../Videos/Kampuchea_krom.MOV",
            'model_path': "../Version1.pt",
            'mask_path': "project.png",
            'output_path': "vehicle_countsversion2.txt",
            'output_log': "vehicle_detection.log",
            'interval': 10,
            'confidence_threshold': 0.3,
            'limits': [250, 267, 677, 267],
            'frame_size': (960, 540)
        }
        
        # Validate configuration
        validate_config(config)
        
        # Validate all required files
        validate_video_source(config['video_path'])
        validate_model_file(config['model_path'])
        validate_file_exists(config['mask_path'])
        
        # Sanitize output path
        output_file_path = sanitize_output_path(config['output_path'])
        
        # Load video
        cap = cv2.VideoCapture(config['video_path'])
        if not cap.isOpened():
            logger.error("Failed to open video capture")
            raise RuntimeError("Cannot open video")
        
        logger.info("Video loaded successfully")
        
        # Check for GPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Load YOLO model
        model = YOLO(config['model_path']).to(device)
        logger.info(f"Model loaded successfully: {config['model_path']}")

        # COCO class names
        classNames = [
            "person", "bicycle", "car", "motorcycle", "airplane", "tuk-tuk", "train", "truck", "boat",
            "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
            "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
            "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat",
            "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
            "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli",
            "carrot", "hot dog", "pizza", "donut", "cake", "chair", "sofa", "potted plant", "bed",
            "dining table", "toilet", "tvmonitor", "laptop", "mouse", "remote", "keyboard", "cell phone",
            "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
            "teddy bear", "hair drier", "toothbrush"
        ]

        # Load and validate mask image
        mask = cv2.imread(config['mask_path'])
        if mask is None:
            logger.error(f"Failed to load mask: {config['mask_path']}")
            raise ValueError("Mask image could not be loaded")
        mask = cv2.resize(mask, config['frame_size'])
        logger.info("Mask loaded successfully")

        # Initialize SORT tracker
        tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)
        logger.info("Tracker initialized")

        # Line crossing limits
        limits = config['limits']
        totalCar = []
        totalBus = []
        totalVan = []
        totalMotor = []
        totalBicycle = []

        freeze_frame = False
        img_frozen = None

        # Initialize database for storing vehicle counts
        db = None
        if VehicleCountDatabase:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'vehicle_detection.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            try:
                db = VehicleCountDatabase(db_path=db_path)
                print(f" Database initialized: {db_path}")
                logger.info(f"Database initialized: {db_path}")
            except Exception as e:
                print(f" Database initialization failed: {e}")
                logger.error(f"Database initialization failed: {e}")
                db = None

        # Time tracking for interval writing and database saves
        output_file = open(output_file_path, "w")
        start_time = time.time()
        interval = config['interval']
        last_write_time = 0
        last_db_save = time.time()
        db_save_interval = 5  # Save to database every 5 seconds
        frame_count = 0

        logger.info("Processing started")

        while True:
            try:
                if not freeze_frame:
                    success, img = cap.read()
                    if not success:
                        logger.info("Video processing completed")
                        break
                    img_frozen = img.copy()
                    img = cv2.resize(img, config['frame_size'])
                else:
                    img = img_frozen

                if img is None:
                    logger.warning("Empty frame detected")
                    break
                
                frame_count += 1
                
                imgRegion = cv2.bitwise_and(img, mask)
                results = model(imgRegion, stream=True)
                detections = np.empty((0, 6))

                for r in results:
                    for box in r.boxes:
                        try:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            w, h = x2 - x1, y2 - y1
                            conf = math.ceil(box.conf[0] * 100) / 100
                            cls = int(box.cls[0])
                            
                            if cls >= len(classNames):
                                logger.warning(f"Invalid class index: {cls}")
                                continue
                            
                            currentClass = classNames[cls]

                            if currentClass in ["car", "bus", "truck", "tuk-tuk", "motorcycle", "bicycle"] and conf > config['confidence_threshold']:
                                currentArray = np.array([x1, y1, x2, y2, conf, cls])
                                detections = np.vstack((detections, currentArray))
                        except Exception as e:
                            logger.warning(f"Error processing detection: {str(e)}")
                            continue

                resultsTracker = tracker.update(detections[:, :5])

                cv2.line(img, (limits[0], limits[1]), (limits[2], limits[3]), (0, 0, 255), 5)

                for result in resultsTracker:
                    try:
                        x1, y1, x2, y2, id = map(int, result)
                        w, h = x2 - x1, y2 - y1
                        cvzone.cornerRect(img, (x1, y1, w, h), l=9, rt=2, colorR=(255, 0, 255))
                        cvzone.putTextRect(img, f' {int(id)}', (max(0, x1), max(35, y1)), scale=2, thickness=2, offset=10)

                        cx, cy = x1 + w // 2, y1 + h // 2
                        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

                        best_iou = 0
                        best_detection = None
                        for det in detections:
                            dx1, dy1, dx1_g, dy2_g, conf, cls = map(int, det)
                            iou_val = calculate_iou((x1, y1, x2, y2), (dx1, dy1, dx1_g, dy2_g))
                            if iou_val > best_iou:
                                best_iou = iou_val
                                best_detection = det

                        if best_detection is not None:
                            cls = int(best_detection[5])
                            if cls >= len(classNames):
                                logger.warning(f"Invalid class index in tracking: {cls}")
                                continue
                            currentClass = classNames[cls]

                            if limits[0] < cx < limits[2] and limits[1] - 15 < cy < limits[1] + 15:
                                if currentClass == "car" and id not in totalCar:
                                    totalCar.append(id)
                                    cv2.line(img, (limits[0], limits[1]), (limits[2], limits[3]), (0, 255, 0), 5)
                                elif currentClass == "bus" and id not in totalBus:
                                    totalBus.append(id)
                                    cv2.line(img, (limits[0], limits[1]), (limits[2], limits[3]), (0, 255, 0), 5)
                                elif (currentClass == "truck" or currentClass == "tuk-tuk") and id not in totalVan:
                                    totalVan.append(id)
                                    cv2.line(img, (limits[0], limits[1]), (limits[2], limits[3]), (0, 255, 0), 5)
                                elif currentClass == "motorcycle" and id not in totalMotor:
                                    totalMotor.append(id)
                                    cv2.line(img, (limits[0], limits[1]), (limits[2], limits[3]), (0, 255, 0), 5)
                                elif currentClass == "bicycle" and id not in totalBicycle:
                                    totalBicycle.append(id)
                                    cv2.line(img, (limits[0], limits[1]), (limits[2], limits[3]), (0, 255, 0), 5)
                    except Exception as e:
                        logger.warning(f"Error processing tracker result: {str(e)}")
                        continue

                # Check if interval has passed and write counts
                current_time = time.time() - start_time
                if current_time - last_write_time >= interval:
                    output_file.write(f"Time {current_time:.1f}s: Cars: {len(totalCar)}, Vans: {len(totalVan)}, Motors: {len(totalMotor)}, Buses: {len(totalBus)}, Bicycles: {len(totalBicycle)}\n")
                    output_file.flush()
                    last_write_time = current_time
                    logger.info(f"Counts written at {current_time:.1f}s - Cars: {len(totalCar)}, Vans: {len(totalVan)}, Motors: {len(totalMotor)}, Buses: {len(totalBus)}, Bicycles: {len(totalBicycle)}")

                # Save to database at regular intervals
                current_time_real = time.time()
                if db and (current_time_real - last_db_save) >= db_save_interval:
                    try:
                        vehicle_counts = {
                            'cars': len(totalCar),
                            'vans': len(totalVan),
                            'motors': len(totalMotor),
                            'buses': len(totalBus),
                            'bicycles': len(totalBicycle)
                        }
                        success = db.save_vehicle_counts(vehicle_counts)
                        if success:
                            print(f" Saved to DB - Cars: {vehicle_counts['cars']}, Vans: {vehicle_counts['vans']}, Motors: {vehicle_counts['motors']}, Buses: {vehicle_counts['buses']}, Bicycles: {vehicle_counts['bicycles']}")
                            logger.info(f"Saved to database - {vehicle_counts}")
                        last_db_save = current_time_real
                    except Exception as e:
                        print(f" Error saving to database: {e}")
                        logger.error(f"Database save error: {e}")

                cv2.putText(img, f"Cars: {len(totalCar)}", (50, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
                cv2.putText(img, f"Vans: {len(totalVan)}", (50, 100), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
                cv2.putText(img, f"Motors: {len(totalMotor)}", (50, 150), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
                cv2.putText(img, f"Bus: {len(totalBus)}", (50, 200), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)

                cv2.imshow("Image", img)

                key = cv2.waitKey(1) & 0xFF

                if key == ord('q'):
                    logger.info("Processing stopped by user")
                    break
                elif key == ord('f'):
                    freeze_frame = not freeze_frame
                    
            except Exception as e:
                logger.error(f"Error in main loop at frame {frame_count}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"Error: {str(e)}")
    finally:
        # Cleanup
        try:
            if 'output_file' in locals():
                output_file.close()
            if 'cap' in locals():
                cap.release()
            cv2.destroyAllWindows()
            
            # Save final counts to database
            if db:
                try:
                    final_counts = {
                        'cars': len(totalCar),
                        'vans': len(totalVan),
                        'motors': len(totalMotor),
                        'buses': len(totalBus),
                        'bicycles': len(totalBicycle)
                    }
                    db.save_vehicle_counts(final_counts)
                    print(f"\n Final counts saved to database:")
                    print(f"   Cars: {final_counts['cars']}")
                    print(f"   Vans: {final_counts['vans']}")
                    print(f"   Motors: {final_counts['motors']}")
                    print(f"   Buses: {final_counts['buses']}")
                    print(f"   Bicycles: {final_counts['bicycles']}")
                    logger.info(f"Final counts saved to database - {final_counts}")
                except Exception as e:
                    print(f" Error saving final counts: {e}")
                    logger.error(f"Error saving final counts: {e}")
            
            logger.info("Resources cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

if __name__ == "__main__":
    main()