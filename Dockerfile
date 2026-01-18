FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and PyGame
RUN apt-get update && apt-get install -y \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsdl2-dev \
    libsdl2-image-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Create requirements.txt if it doesn't exist
RUN pip install --no-cache-dir \
    opencv-python==4.8.1.78 \
    ultralytics==8.0.200 \
    torch==2.1.1 \
    torchvision==0.16.1 \
    numpy==1.24.3 \
    pygame==2.6.1 \
    scipy==1.15.3 \
    cvzone==1.6.1 \
    filterpy==1.4.5 \
    websockets==12.0

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:0

# Create data directory for database
RUN mkdir -p /app/data /app/security_logs

# Default command - run vehicle counting
CMD ["python", "vehicle_counting_integrated/PassedCounting.py"]