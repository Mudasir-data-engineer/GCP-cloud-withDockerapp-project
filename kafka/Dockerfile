# Use a minimal Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy only what's needed
COPY consumer.py .

# Install only what's necessary
RUN pip install --no-cache-dir kafka-python

# Run the consumer
CMD ["python", "consumer.py"]
