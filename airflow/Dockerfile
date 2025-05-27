
FROM apache/airflow:2.7.3

USER root


RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev build-essential libffi-dev libssl-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


COPY requirements.txt /


USER airflow
RUN pip install --upgrade pip wheel setuptools==66.0.0 --no-cache-dir && \
    pip install --no-cache-dir -r /requirements.txt

    
USER root

COPY airflow/dags /opt/airflow/dags

COPY airflow/dags/gcs_keyfile.json /opt/airflow/dags/gcs_keyfile.json



RUN chown -R airflow: /opt/airflow/dags /opt/airflow/logs


USER airflow
