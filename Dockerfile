# Use a more recent and secure base image
FROM python:3.12-alpine3.20

# Install system dependencies
RUN apk add --no-cache \
    libffi \
    ffmpeg \
    libopusenc \
    build-base \
    python3-dev \
    libffi-dev \
    musl-dev \
    git

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app .

# Use exec form to avoid shell wrapping
ENTRYPOINT ["python", "main.py"]
