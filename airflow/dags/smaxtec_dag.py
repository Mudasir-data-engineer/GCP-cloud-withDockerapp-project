from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.http.sensors.http import HttpSensor
from datetime import datetime
import subprocess
import requests

# Custom functions
def call_fake_api():
    url = "http://fake-api:5000/cow-data"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"API call failed with status {response.status_code}")

def run_producer():
    try:
        result = subprocess.run(
            ["python", "/opt/airflow/kafka/producer.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20  # kill after 20 seconds (adjust as needed)
        )
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        result.check_returncode()  # raises error if exit code != 0
    except subprocess.CalledProcessError as e:
        print("Producer script failed with return code:", e.returncode)
        print("Output:\n", e.output)
        print("Error Output:\n", e.stderr)
        raise
    except subprocess.TimeoutExpired:
        print("Producer script timed out.")
        raise


def run_consumer():
    subprocess.run(["python", "/opt/airflow/kafka/consumer.py"], check=True)

def run_pipeline_processor():
    subprocess.run(["python", "/opt/airflow/consumer/consumer.py"], check=True)

# DAG definition
with DAG(
    dag_id='smaxtec_dag',
    start_date=datetime(2025, 5, 1),
    schedule_interval='*/30 * * * *',  # Every 30 minutes
    catchup=False
) as dag:

    api_health_check = HttpSensor(
        task_id='api_health_check',
        http_conn_id='api_connection',  # Define this in Airflow UI
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

    # Task pipeline
    api_health_check >> call_fake_api_task >> produce_task >> consume_task >> pipeline_processor_task
