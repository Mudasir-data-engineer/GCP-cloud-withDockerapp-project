# airflow/Dockerfile
FROM apache/airflow:2.7.3

USER root

# Install dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev build-essential libffi-dev libssl-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt /

# Switch to airflow and install Python packages
USER airflow
RUN pip install --upgrade pip wheel setuptools==66.0.0 --no-cache-dir && \
    pip install --no-cache-dir -r /requirements.txt && \
    pip install --no-cache-dir scikit-learn && \
    pip install 'pyarrow>=10.0.1,<10.1.0'

# Copy DAGs, scripts, and GCS key
USER root
COPY airflow/dags /opt/airflow/dags
COPY airflow/dags/scripts /opt/airflow/dags/scripts
COPY airflow/dags/gcs_keyfile.json /opt/airflow/dags/gcs_keyfile.json

# Fix permissions
RUN chown -R airflow: /opt/airflow/dags /opt/airflow/logs

# Set working user
USER airflow
