FROM apache/airflow:2.5.1

USER root

# Install required dependencies for psycopg2
RUN apt-get update && apt-get install -y libpq-dev

COPY ../requirements.txt /requirements.txt

USER airflow

RUN pip install --no-cache-dir -r /requirements.txt
