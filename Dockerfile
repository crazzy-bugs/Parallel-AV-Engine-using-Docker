# Use an official Ubuntu base image
FROM ubuntu:20.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install required packages
RUN apt-get update && \
    apt-get install -y \
    inotify-tools \
    python3 \
    python3-pip \
    net-tools \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install requests

# Download and install eScan (placeholder - you'll need to replace with actual installation)
RUN wget https://example.com/escan-antivirus-linux.deb -O /tmp/escan.deb && \
    dpkg -i /tmp/escan.deb || apt-get -f install -y && \
    rm /tmp/escan.deb

# Create a working directory
WORKDIR /app

# Copy the Python script into the container
COPY monitor.py /app/monitor.py

# Ensure the target folder exists in the container
RUN mkdir -p /mnt/target-folder /storage

# Expose storage and monitoring folders
VOLUME ["/mnt/target-folder", "/storage"]

# Entry point to run the monitoring script
ENTRYPOINT ["python3", "/app/monitor.py"]