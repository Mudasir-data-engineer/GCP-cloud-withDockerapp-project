from airflow import DAG
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import BigQueryToGCSOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from datetime import datetime, timedelta

default_args = {
    "start_date": datetime(2025, 5, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="feature_scaling_dag",
    schedule_interval="0 1 * * *",   # every day 01:00
    catchup=False,
    default_args=default_args,
    tags=["ml", "scaling"],
) as dag:

    # a. pull yesterday’s hourly rows into JSON
    bq_extract = BigQueryToGCSOperator(
        task_id="bq_extract",
        source_project_dataset_table="""
            (SELECT *
             FROM `smaxtec_dataset.hourly_features_v`
             WHERE DATE(hour_ts) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY))
        """,
        destination_cloud_storage_uris=[
            "gs://smaxtec-project-bucket/tmp/yesterday.json"
        ],
        export_format="NEWLINE_DELIMITED_JSON",
        print_header=False,
        gcp_conn_id="google_cloud_default",
    )

    # b. clean & scale (runs scripts/scale_features.py inside a python:3.11 container)
    scale = DockerOperator(
        task_id="scale_features",
        image="python:3.11",
        command=[
            "python",
            "/opt/airflow/scripts/scale_features.py",
            "--input",  "gs://smaxtec-project-bucket/tmp/yesterday.json",
            "--output", "gs://smaxtec-project-bucket/tmp/yesterday_scaled.json",
            "--scaler", "gs://smaxtec-project-bucket/models/scaler.joblib",
        ],
        auto_remove=True,
        network_mode="bridge",
        mounts=["./scripts:/opt/airflow/scripts"],   # maps host scripts/ into the container
    )

    # c. load scaled JSON back to BigQuery
    load = GCSToBigQueryOperator(
        task_id="gcs_to_bq",
        bucket="smaxtec-project-bucket",
        source_objects=["tmp/yesterday_scaled.json"],
        destination_project_dataset_table="smaxtec_dataset.hourly_scaled",
        source_format="NEWLINE_DELIMITED_JSON",
        write_disposition="WRITE_APPEND",
        time_partitioning={"type": "DAY", "field": "hour_ts"},
        gcp_conn_id="google_cloud_default",
    )

    # task order
    bq_extract >> scale >> load
