# Multi-stage build for optimal image size
FROM python:3.11-bookworm as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    libvpx-dev \
    libopus-dev \
    libsrtp2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Production stage
FROM python:3.11-bookworm

# Install runtime dependencies and Playwright requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    libvpx-dev \
    libopus-dev \
    libsrtp2-dev \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    libglib2.0-0 \
    libgtk-3-0 \
    fonts-liberation \
    libu2f-udev \
    libvulkan1 \
    xdg-utils \
    wget \
    # Audio support for Linux
    pulseaudio \
    pulseaudio-utils \
    alsa-utils \
    libasound2-plugins \
    && rm -rf /var/lib/apt/lists/*

# Copy Python environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy Playwright browsers from builder
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Create app directory
WORKDIR /app

# Copy application code
COPY . .

# Create non-root user for security and configure PulseAudio
RUN useradd -m -u 1000 jiomosa && \
    chown -R jiomosa:jiomosa /app && \
    mkdir -p /home/jiomosa/.cache/ms-playwright && \
    cp -r /root/.cache/ms-playwright/* /home/jiomosa/.cache/ms-playwright/ && \
    chown -R jiomosa:jiomosa /home/jiomosa/.cache && \
    # Configure PulseAudio for non-root user
    mkdir -p /home/jiomosa/.config/pulse && \
    mkdir -p /run/user/1000 && \
    chown -R jiomosa:jiomosa /home/jiomosa/.config && \
    chown -R jiomosa:jiomosa /run/user/1000 && \
    # Create PulseAudio startup script
    echo '#!/bin/bash\n\
# Setup runtime directory\n\
export XDG_RUNTIME_DIR=/run/user/1000\n\
mkdir -p $XDG_RUNTIME_DIR\n\
chmod 700 $XDG_RUNTIME_DIR\n\
\n\
# Start PulseAudio daemon\n\
pulseaudio -D --exit-idle-time=-1 --system=false --disallow-exit 2>/dev/null\n\
sleep 2\n\
\n\
# Create virtual sink for browser audio capture\n\
pactl load-module module-null-sink sink_name=browser_audio sink_properties=device.description=Browser_Audio 2>/dev/null || true\n\
pactl set-default-sink browser_audio 2>/dev/null || true\n\
\n\
echo "PulseAudio setup complete"\n\
pactl info 2>/dev/null || echo "PulseAudio failed to start"\n\
\n\
# Start the application\n\
exec "$@"' > /home/jiomosa/start.sh && \
    chmod +x /home/jiomosa/start.sh && \
    chown jiomosa:jiomosa /home/jiomosa/start.sh

USER jiomosa

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/home/jiomosa/.cache/ms-playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    XDG_RUNTIME_DIR=/run/user/1000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with PulseAudio setup
ENTRYPOINT ["/home/jiomosa/start.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

