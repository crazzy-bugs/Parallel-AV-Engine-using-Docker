#!/bin/bash

# Start ClamAV daemon
service clamav-daemon start

# Start ClamAV freshclam (for updates)
service clamav-freshclam start

# Run the main application
python3 monitor.py