# Dockerfile for kafka-consumer
FROM python:3.11-slim

WORKDIR /app

# Install any dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port if needed
EXPOSE 5000

# Command to run the consumer
CMD ["python", "consumer.py"]
