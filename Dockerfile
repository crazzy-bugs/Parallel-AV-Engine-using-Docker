# Use Ubuntu as the base image
FROM ubuntu:22.04

# Set the working directory
WORKDIR /app

# Install Python and system dependencies, including ClamAV and ClamAV daemon
RUN apt-get update && \
    apt-get install -y \
        python3 \
        python3-pip \
        clamav \
        clamav-daemon \
        clamav-freshclam \
        clamav-base && \
    apt-get clean

# Start and configure ClamAV services
RUN sed -i 's/^Example/#Example/' /etc/clamav/clamd.conf && \
    sed -i 's/^Example/#Example/' /etc/clamav/freshclam.conf && \
    freshclam

# Copy the application code and requirements
COPY . /app
COPY requirements.txt /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose port (if needed for ClamAV daemon or app)
EXPOSE 3310

# Start ClamAV daemon and run the Python application
CMD service clamav-daemon start && \
    service clamav-freshclam start && \
    python3 monitor.py
