FROM apache/airflow:2.7.3  # Airflow with Python 3.11

# Switch to root for system-level installs
USER root

# Install system dependencies (e.g., for psycopg2 / Postgres)
RUN apt-get update && apt-get install -y libpq-dev

# Copy requirements and credentials
COPY ../requirements.txt /requirements.txt
COPY dags/gcs_keyfile.json /opt/airflow/dags/gcs_keyfile.json

# Install Python packages
RUN pip install --no-cache-dir -r /requirements.txt
RUN pip install --no-cache-dir kafka-python

# Switch back to airflow user
USER airflow
