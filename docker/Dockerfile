FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    linux-headers-generic \
    libportaudio2 \         
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create workdir
RUN mkdir /workdir

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WORK_DIR=/workdir

# Default command
CMD ["python", "project_manager.py"]
