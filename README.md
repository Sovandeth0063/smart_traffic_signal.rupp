# Vehicle Detection and Counting using YOLO

This project uses a YOLO (You Only Look Once) model to detect and count vehicles in images and video streams. The project is divided into several Python scripts, each with a specific purpose.

## Project Process

1.  **YOLO Model Training:** A YOLO model was trained on a dataset of vehicle images to learn to identify and locate different types of vehicles.
2.  **Vehicle Counting:**
    *   `PassedCounting.py`: This script counts the number of vehicles that pass a predefined limit line in a video stream.
    *   `InStopCounting&PassedCounting.py`: This script extends the functionality to not only count vehicles passing the limit line but also to count vehicles that are stopped.

## Python File Explanations

### `yolo_pic.py`

*   **Purpose:** This script uses the trained YOLO model to perform vehicle detection on a static image.
*   **Logic:**
    1.  Loads the trained YOLO model.
    2.  Reads an input image.
    3.  Performs object detection on the image to identify vehicles.
    4.  Draws bounding boxes around the detected vehicles.
    5.  Displays the image with the detected vehicles.

### `yolo_webcam.py`

*   **Purpose:** This script uses the trained YOLO model to perform real-time vehicle detection using a webcam feed.
*   **Logic:**
    1.  Loads the trained YOLO model.
    2.  Captures video frames from a webcam.
    3.  For each frame, it performs object detection to identify vehicles.
    4.  Draws bounding boxes around the detected vehicles in real-time.
    5.  Displays the video feed with the detections.

### `car_counting/Car_counting_test.py`

*   **Purpose:** This script is a test file for the car counting functionality. It likely contains code to test the accuracy and performance of the counting algorithms.
*   **Logic:** The logic would depend on the specific tests implemented. It could involve:
    *   Running the counting scripts on a sample video with a known number of vehicles.
    *   Comparing the script's output with the ground truth to calculate accuracy.

### `car_counting/InStopCounting&PassedCounting.py`

*   **Purpose:** This script counts vehicles that are stopped and vehicles that pass a specific line in a video.
*   **Logic:**
    1.  It uses the YOLO model to detect vehicles in each frame of a video.
    2.  It uses the `sort.py` tracker to track each detected vehicle across frames.
    3.  **Passing Logic:** A line is defined in the video frame. If a vehicle's bounding box crosses this line, a counter is incremented.
    4.  **Stopping Logic:** The script monitors the position of each tracked vehicle. If a vehicle's position does not change significantly over a certain number of frames, it is considered "stopped," and a counter for stopped vehicles is incremented.

### `car_counting/PassedCounting.py`

*   **Purpose:** This script is focused solely on counting vehicles that pass a designated line in a video.
*   **Logic:**
    1.  It uses the YOLO model to detect vehicles in each frame.
    2.  It uses the `sort.py` tracker to assign a unique ID to each detected vehicle and track its movement.
    3.  A horizontal or vertical line is defined in the frame.
    4.  The script checks the coordinates of each tracked vehicle. When a vehicle's bounding box intersects with the predefined line, the passing vehicle counter is incremented.
