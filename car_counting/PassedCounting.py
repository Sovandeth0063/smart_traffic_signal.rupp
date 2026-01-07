import torch
import numpy as np
from ultralytics import YOLO
import cv2
import cvzone
import math
from sort import Sort

def calculate_iou(box1, box2):
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

    return inter_area / union_area

# Load video
cap = cv2.VideoCapture("Videos/Kampuchea_krom.MOV")

# Check for GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load YOLO model
model = YOLO("yolo11m.pt").to(device)

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

# Load mask image
mask = cv2.imread("car_counting/project.png")
mask = cv2.resize(mask, (960, 540))

# Initialize SORT tracker
tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3) # Intersection over Union Treshold

# Line crossing limits
# [start_x, start_y, end_x, end_y]
limits = [250, 267, 677, 267]
totalCar = []
totalBus = []
totalVan = []
totalMotor = []
totalBicycle = []

freeze_frame = False
img_frozen = None

while True:
    if not freeze_frame:
        success, img = cap.read()
        if not success:
            break
        img_frozen = img.copy()
        img = cv2.resize(img, (960, 540)) # Resize img to match mask dimensions
    else:
        img = img_frozen

    if img is None: # Handle case where video might end while frozen or initial read fails
        break

    imgRegion = cv2.bitwise_and(img, mask) # set the region of interest
    imgGraphics = cv2.imread("car_counting/graphics.png", cv2.IMREAD_UNCHANGED)
    # img = cvzone.overlayPNG(img, imgGraphics, (0, 0))

    results = model(imgRegion, stream=True)
    detections = np.empty((0, 6))

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            w, h = x2 - x1, y2 - y1
            conf = math.ceil(box.conf[0] * 100) / 100
            cls = int(box.cls[0])
            currentClass = classNames[cls]

            if currentClass in ["car", "bus", "truck", "tuk-tuk", "motorcycle", "bicycle"] and conf > 0.3:
                currentArray = np.array([x1, y1, x2, y2, conf, cls])
                detections = np.vstack((detections, currentArray))

    resultsTracker = tracker.update(detections[:, :5])

    cv2.line(img, (limits[0], limits[1]), (limits[2], limits[3]), (0, 0, 255), 5)

    for result in resultsTracker:
        x1, y1, x2, y2, id = map(int, result)
        w, h = x2 - x1, y2 - y1
        cvzone.cornerRect(img, (x1, y1, w, h), l=9, rt=2, colorR=(255, 0, 255))
        cvzone.putTextRect(img, f' {int(id)}', (max(0, x1), max(35, y1)), scale=2, thickness=2, offset=10)

        cx, cy = x1 + w // 2, y1 + h // 2
        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

        # Find the detection with the highest IoU
        best_iou = 0
        best_detection = None
        for det in detections:
            dx1, dy1, dx1_g, dy2_g, conf, cls = map(int, det)
            iou_val = calculate_iou((x1, y1, x2, y2), (dx1, dy1, dx1_g, dy2_g))
            if iou_val > best_iou:
                best_iou = 0
                best_detection = det

        if best_detection is not None:
            cls = int(best_detection[5])
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

    cv2.putText(img, f"Cars: {len(totalCar)}", (50, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
    cv2.putText(img, f"Vans: {len(totalVan)}", (50, 100), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
    cv2.putText(img, f"Motors: {len(totalMotor)}", (50, 150), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
    cv2.putText(img, f"Bus: {len(totalBus)}", (50, 200), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)


    cv2.imshow("Image", img)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('f'):
        freeze_frame = not freeze_frame