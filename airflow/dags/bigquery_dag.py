from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
import os

# DAG Configuration
BUCKET_NAME = 'smaxtec-project-bucket'
DATA_PREFIX = 'cow_data/'
PROCESSED_PREFIX = 'cow_data/processed_folders/'
PROJECT_ID = 'smaxtec-project-gcp'
DATASET = 'smaxtec_dataset'
TABLE = 'smaxtec_data'

# Service account key path
key_path = os.path.join(os.path.dirname(__file__), 'gcs_keyfile.json')

# Default DAG arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def list_unprocessed_folders(**context):
    hook = GCSHook(gcp_conn_id='google_cloud_default', key_file=key_path)
    blobs = hook.list(bucket_name=BUCKET_NAME, prefix=DATA_PREFIX)

    folders = set()
    for blob in blobs:
        parts = blob.split('/')
        if len(parts) > 2 and parts[1] and not blob.startswith(PROCESSED_PREFIX):
            folder = f"{parts[0]}/{parts[1]}/"
            folders.add(folder)

    sorted_folders = sorted(folders)
    print(f"Unprocessed folders: {sorted_folders}")
    return sorted_folders

def move_to_processed_and_cleanup(folder_name, **kwargs):
    hook = GCSHook(gcp_conn_id='google_cloud_default', key_file=key_path)

    src_prefix = f"{DATA_PREFIX}{folder_name}/"
    dest_prefix = f"{PROCESSED_PREFIX}{folder_name}/"

    print(f"Moving from {src_prefix} to {dest_prefix}")

    # List all objects under the folder
    blobs = hook.list(bucket_name=BUCKET_NAME, prefix=src_prefix)

    for blob in blobs:
        filename = blob.split('/')[-1]
        src_path = blob
        dest_path = f"{dest_prefix}{filename}"

        # Copy to processed location
        hook.copy(
            source_bucket=BUCKET_NAME,
            source_object=src_path,
            destination_bucket=BUCKET_NAME,
            destination_object=dest_path
        )
        # Delete original file
        hook.delete(bucket_name=BUCKET_NAME, object_name=src_path)

    print(f"Moved and cleaned up folder: {folder_name}")

# Define the DAG
with DAG(
    dag_id='gcs_to_bigquery_ingestion',
    default_args=default_args,
    schedule_interval='0 0,12 * * *',  # Runs at 00:00 and 12:00
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['gcs', 'bigquery'],
) as dag:

    list_folders_task = PythonOperator(
        task_id='list_unprocessed_folders',
        python_callable=list_unprocessed_folders,
    )

    def create_dynamic_tasks(**kwargs):
        ti = kwargs['ti']
        folders = ti.xcom_pull(task_ids='list_unprocessed_folders')

        if not folders:
            print("No unprocessed folders found.")
            return

        for folder in folders:
            folder_name = folder.rstrip('/').split('/')[-1]
            safe_id = folder_name.replace("-", "_").replace(":", "_")
            source_objects = [f"{folder}batch_{i}.ndjson" for i in range(1, 11)]

            load_task = GCSToBigQueryOperator(
                task_id=f'load_{safe_id}',
                bucket=BUCKET_NAME,
                source_objects=source_objects,
                destination_project_dataset_table=f"{PROJECT_ID}.{DATASET}.{TABLE}",
                source_format='NEWLINE_DELIMITED_JSON',
                write_disposition='WRITE_APPEND',
                autodetect=True,
                gcp_conn_id='google_cloud_default',
                retries=3,
            )
            load_task.dag = dag

            move_task = PythonOperator(
                task_id=f'move_{safe_id}_to_processed',
                python_callable=move_to_processed_and_cleanup,
                op_kwargs={'folder_name': folder_name},
                retries=3,
            )
            move_task.dag = dag

            load_task >> move_task

    generate_tasks = PythonOperator(
        task_id='generate_tasks',
        python_callable=create_dynamic_tasks,
        provide_context=True,
    )

    list_folders_task >> generate_tasks
