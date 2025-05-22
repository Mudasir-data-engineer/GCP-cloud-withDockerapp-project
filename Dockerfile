FROM apache/airflow:2.7.3-python3.11

# Install Python packages as airflow user
USER airflow
RUN pip install --no-cache-dir kafka-python apache-airflow-providers-postgres

# Switch to root for system-level dependencies
USER root
RUN apt-get update && apt-get install -y libpq-dev

# Copy requirements file
COPY airflow/requirements.txt /requirements.txt

# ✅ Make sure the file exists before copying this
COPY airflow/dags/gcs_keyfile.json /opt/airflow/dags/gcs_keyfile.json

# Back to airflow user
USER airflow
RUN pip install --no-cache-dir -r /requirements.txt
