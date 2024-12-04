FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the application code and requirements
COPY . /app
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the application
CMD ["python", "monitor.py"]
