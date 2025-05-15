# dags/smaxtec_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import subprocess
import requests
import logging

def call_fake_api():
    url = "http://fake-api:5000/cow-data"
    try:
        response = requests.get(url)
        response.raise_for_status()
        logging.info(f"API call successful: {response.status_code}")
        logging.info(f"Data: {response.json()}")
    except Exception as e:
        logging.error(f"API call failed: {e}")
        raise

def run_subprocess(command, label):
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )
        logging.info(f"{label} STDOUT: {result.stdout}")
        if result.stderr:
            logging.error(f"{label} STDERR: {result.stderr}")
        result.check_returncode()
    except subprocess.CalledProcessError as e:
        logging.error(f"{label} failed with return code {e.returncode}")
        raise
    except subprocess.TimeoutExpired:
        logging.error(f"{label} timed out.")
        raise

def run_producer():
    logging.info("Running Kafka producer task.")
    run_subprocess(["python", "/opt/airflow/kafka/producer.py"], "Producer")

def run_pipeline_processor():
    logging.info("Running pipeline processor task.")
    run_subprocess(["python", "/opt/airflow/consumer/consumer.py"], "Pipeline Processor")

def check_api_health():
    import time
    max_retries = 6
    for attempt in range(max_retries):
        try:
            response = requests.get("http://fake-api:5000/health", timeout=5)
            if response.status_code == 200:
                logging.info("API is healthy.")
                return
            else:
                logging.warning(f"Health check failed: {response.status_code}")
        except Exception as e:
            logging.warning(f"Health check exception: {e}")
        time.sleep(10)
    raise Exception("API health check failed after multiple retries.")

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    dag_id='smaxtec_dag',
    default_args=default_args,
    start_date=datetime(2025, 5, 1),
    schedule_interval='0 */3 * * *',  # Every 3 hours
    catchup=False
) as dag:

    api_health_check = PythonOperator(
        task_id='api_health_check',
        python_callable=check_api_health
    )

    call_fake_api_task = PythonOperator(
        task_id='call_fake_api',
        python_callable=call_fake_api
    )

    produce_task = PythonOperator(
        task_id='run_producer',
        python_callable=run_producer
    )

    pipeline_processor_task = PythonOperator(
        task_id='pipeline_processor',
        python_callable=run_pipeline_processor
    )

    # Define task dependencies
    api_health_check >> call_fake_api_task >> produce_task >> pipeline_processor_task
