# Install Ultralytics YOLO library if you haven't
# pip install ultralytics

from ultralytics import YOLO
import cv2

# Load a pre-trained YOLOv8 model (YOLOv8n = nano, smallest model)
model = YOLO("yolo11l.pt")  

# Load your image
image_path = "image.jpg" 
image = cv2.imread(image_path)

results = model(image_path)

# Print detected objects
for result in results:
    print(result.boxes)  # Bounding boxes
    print(result.names)  # Detected class names

# Visualize results
results[0].plot()  # Plot detection on image
cv2.imshow("YOLO Detection", results[0].plot())
cv2.waitKey(0)
cv2.destroyAllWindows()
