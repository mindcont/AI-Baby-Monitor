# Use DaoCloud mirror for the official Python image to avoid Docker Hub connectivity issues in China.
FROM m.daocloud.io/docker.io/library/python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DOCKER_CONTAINER=1
# Use a domestic PyPI mirror for dependency installation.
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

# Install system dependencies using the Aliyun Debian mirror.
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g; s|security.debian.org|mirrors.aliyun.com|g' \
        /etc/apt/sources.list.d/debian.sources /etc/apt/sources.list 2>/dev/null || true \
    && apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    ffmpeg \
    git \
    wget \
    curl \
    ca-certificates \
    python3-dbus \
    dbus-x11  \
    && rm -rf /var/lib/apt/lists/*

# Create app directory and non-root user
RUN useradd -m -u 1000 appuser
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/data/recordings \
    /app/data/logs \
    /app/data/cache \
    && chown -R appuser:appuser /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install the threaded WebSocket backend separately so changes here do not
# invalidate the large PyTorch/Ultralytics dependency layer above.
RUN pip install --no-cache-dir simple-websocket==1.1.0

# Copy application code
COPY . .

# Change ownership of app directory and all subfolders after copying code
RUN chown -R appuser:appuser /app /app/data /app/data/recordings /app/data/logs /app/data/cache

# Switch to non-root user
USER appuser

ENV YOLO_CONFIG_DIR=/app/data/cache/ultralytics
RUN mkdir -p /app/data/cache/ultralytics && chown -R appuser:appuser /app/data/cache/ultralytics

# Create .env file template if it doesn't exist
RUN if [ ! -f .env ]; then \
    echo "RTSP_USERNAME=username" > .env && \
    echo "RTSP_PASSWORD=password" >> .env && \
    echo "RTSP_IP=192.168.1.3" >> .env && \
    echo "RTSP_PORT=554" >> .env && \
    echo "RTSP_STREAM=stream1" >> .env; \
    fi

# Expose Flask port (using less common port)
EXPOSE 8847

RUN mkdir -p /app/baby-monitor/snapshots && chown -R appuser:appuser /app/baby-monitor/snapshots
RUN mkdir -p /app/baby-monitor/recordings && chown -R appuser:appuser /app/baby-monitor/recordings
RUN mkdir -p /app/baby-monitor/logs && chown -R appuser:appuser /app/baby-monitor/logs
RUN mkdir -p /app/baby-monitor/cache && chown -R appuser:appuser /app/baby-monitor/cache
RUN mkdir -p /app/baby-monitor/database && chown -R appuser:appuser /app/baby-monitor/database

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8847/health || exit 1

# Default command - run Flask in production mode with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8847", "--workers", "1", "--worker-class", "gthread", "--threads", "8", "--timeout", "300", "app:app"]
