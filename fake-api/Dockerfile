# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install pip and upgrade it (always safe to upgrade)
RUN pip install --upgrade pip

# Copy only requirements first (better cache optimization)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of your application
COPY . .

# Expose the port where the app will run
EXPOSE 5000

# Define environment variables (optional but good practice)
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "app.py"]
