from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.http.sensors.http import HttpSensor
from datetime import datetime
import subprocess
import requests


def call_fake_api():
    url = "http://fake-api:5000/cow-data"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"API call failed with status {response.status_code}")
    print(f"API call successful: {response.status_code}", flush=True)
    print(f"Data: {response.text}", flush=True)


def run_producer():
    try:
        result = subprocess.run(
            ["python", "/opt/airflow/kafka/producer.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20
        )
        print("Producer STDOUT:", result.stdout, flush=True)
        print("Producer STDERR:", result.stderr, flush=True)
        result.check_returncode()
    except subprocess.CalledProcessError as e:
        print("Producer script failed:", e.returncode, flush=True)
        print("Error Output:\n", e.stderr, flush=True)
        raise
    except subprocess.TimeoutExpired:
        print("Producer script timed out.", flush=True)
        raise


def run_consumer():
    try:
        result = subprocess.run(
            ["python", "/opt/airflow/kafka/consumer.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("Consumer STDOUT:", result.stdout, flush=True)
        print("Consumer STDERR:", result.stderr, flush=True)
        result.check_returncode()
    except subprocess.CalledProcessError as e:
        print("Consumer script failed:", e.returncode, flush=True)
        print("Error Output:\n", e.stderr, flush=True)
        raise


def run_pipeline_processor():
    try:
        result = subprocess.run(
            ["python", "/opt/airflow/consumer/consumer.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("Pipeline Processor STDOUT:", result.stdout, flush=True)
        print("Pipeline Processor STDERR:", result.stderr, flush=True)
        result.check_returncode()
    except subprocess.CalledProcessError as e:
        print("Pipeline processor failed:", e.returncode, flush=True)
        print("Error Output:\n", e.stderr, flush=True)
        raise


with DAG(
    dag_id='smaxtec_dag',
    start_date=datetime(2025, 5, 1),
    schedule_interval='*/30 * * * *',
    catchup=False
) as dag:

    api_health_check = HttpSensor(
        task_id='api_health_check',
        http_conn_id='api_connection',
        endpoint='cow-data',
        poke_interval=10,
        timeout=60
    )

    call_fake_api_task = PythonOperator(
        task_id='call_fake_api',
        python_callable=call_fake_api
    )

    produce_task = PythonOperator(
        task_id='run_producer',
        python_callable=run_producer
    )

    consume_task = PythonOperator(
        task_id='run_consumer',
        python_callable=run_consumer
    )

    pipeline_processor_task = PythonOperator(
        task_id='pipeline_processor',
        python_callable=run_pipeline_processor
    )

    api_health_check >> call_fake_api_task >> produce_task >> consume_task >> pipeline_processor_task
