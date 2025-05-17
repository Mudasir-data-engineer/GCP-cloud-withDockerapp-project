from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook
import os

# === Configuration ===
BUCKET_NAME      = 'smaxtec-project-bucket'
DATA_PREFIX      = 'cow_data/'
PROCESSED_PREFIX = 'cow_data/processed_folders/'
PROJECT_ID       = 'smaxtec-project-gcp'
DATASET          = 'smaxtec_dataset'
TABLE            = 'smaxtec_data_part'          # new partitioned+clustered table
GCP_CONN_ID      = 'google_cloud_default'
KEY_FILE         = os.path.join(os.path.dirname(__file__), 'gcs_keyfile.json')

# === Explicit BigQuery schema (matches smaxtec_data_part) ===
BQ_SCHEMA = [
    {"name": "event_ts",             "type": "TIMESTAMP", "mode": "NULLABLE"},
    {"name": "temperature",          "type": "FLOAT",     "mode": "NULLABLE"},
    {"name": "humidity",             "type": "FLOAT",     "mode": "NULLABLE"},
    {"name": "activity_level",       "type": "FLOAT",     "mode": "NULLABLE"},
    {"name": "heart_rate",           "type": "INTEGER",   "mode": "NULLABLE"},
    {"name": "rumination_minutes",   "type": "INTEGER",   "mode": "NULLABLE"},
    {"name": "location_x",           "type": "FLOAT",     "mode": "NULLABLE"},
    {"name": "location_y",           "type": "FLOAT",     "mode": "NULLABLE"},
    {"name": "milk_yield",           "type": "FLOAT",     "mode": "NULLABLE"},
    {"name": "is_ruminating",        "type": "BOOLEAN",   "mode": "NULLABLE"},
    {"name": "sensor_id_transformed","type": "INTEGER",   "mode": "NULLABLE"},
    {"name": "cow_id",               "type": "INTEGER",   "mode": "NULLABLE"},
]

# === Default DAG args ===
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# === Helper: list unprocessed folders ===
def list_unprocessed_folders():
    hook = GCSHook(gcp_conn_id=GCP_CONN_ID, key_file=KEY_FILE)
    blobs = hook.list(bucket_name=BUCKET_NAME, prefix=DATA_PREFIX)
    folders = set()
    for blob in blobs:
        parts = blob.split('/')
        if len(parts) > 2 and parts[1] and not blob.startswith(PROCESSED_PREFIX):
            folders.add(f"{parts[0]}/{parts[1]}/")
    return sorted(folders)

# === Helper: move loaded files to processed/ ===
def move_to_processed_and_cleanup(folder_name, **_):
    hook = GCSHook(gcp_conn_id=GCP_CONN_ID, key_file=KEY_FILE)
    src_prefix  = f"{DATA_PREFIX}{folder_name}/"
    dest_prefix = f"{PROCESSED_PREFIX}{folder_name}/"
    for blob in hook.list(bucket_name=BUCKET_NAME, prefix=src_prefix):
        filename  = blob.split('/')[-1]
        hook.copy(
            source_bucket=BUCKET_NAME, source_object=blob,
            destination_bucket=BUCKET_NAME, destination_object=f"{dest_prefix}{filename}"
        )
        hook.delete(bucket_name=BUCKET_NAME, object_name=blob)
    print(f"✅ Moved and cleaned up folder: {folder_name}")

# === DAG Definition ===
with DAG(
    dag_id='gcs_to_bigquery_ingestion',
    default_args=default_args,
    schedule_interval='0 0,12 * * *',   # every 12 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['gcs', 'bigquery'],
) as dag:

    folders = list_unprocessed_folders()
    if not folders:
        print("No unprocessed folders found.")
    else:
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
                autodetect=False,
                schema_fields=BQ_SCHEMA,
                ignore_unknown_values=True,   # skip extra fields
                max_bad_records=5,            # skip up to 5 malformed rows per file
                gcp_conn_id=GCP_CONN_ID,
                retries=3,
            )

            move_task = PythonOperator(
                task_id=f'move_{safe_id}_to_processed',
                python_callable=move_to_processed_and_cleanup,
                op_kwargs={'folder_name': folder_name},
                retries=3,
            )

            load_task >> move_task
