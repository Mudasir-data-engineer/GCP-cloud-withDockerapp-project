from airflow import DAG
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import BigQueryToGCSOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from datetime import datetime, timedelta

default_args = {"start_date": datetime(2025,5,1), "retries":1, "retry_delay": timedelta(minutes=5)}

with DAG(
    dag_id="clustering_dag",
    schedule_interval="30 2 * * *",   # 02:30—after scaling DAG (01:00)
    catchup=False,
    default_args=default_args,
    tags=["ml","clustering"],
) as dag:

    export_scaled = BigQueryToGCSOperator(
    task_id="export_scaled",
    source_project_dataset_table="""
        (SELECT *
         FROM `smaxtec_dataset.hourly_scaled`
         WHERE DATE(hour_ts) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY))
    """,
    destination_cloud_storage_uris=[
        "gs://smaxtec-project-bucket/tmp/yesterday_scaled.json"
    ],
    export_format="NEWLINE_DELIMITED_JSON",
    print_header=False,
    gcp_conn_id="google_cloud_default",
)

    train = DockerOperator(
        task_id="kmeans_train",
        image="python:3.11",
        command=[
            "python","/opt/airflow/scripts/train_kmeans.py",
            "--data","gs://smaxtec-project-bucket/tmp/yesterday_scaled.json",
            "--model-out","gs://smaxtec-project-bucket/models/kmeans.joblib",
            "--clusters-out","gs://smaxtec-project-bucket/tmp/yesterday_clusters.json"
        ],
        auto_remove=True,
        network_mode="bridge",
        mounts=["./scripts:/opt/airflow/scripts"],
    )

    load_clusters = GCSToBigQueryOperator(
    task_id="load_clusters",
    bucket="smaxtec-project-bucket",
    source_objects=["tmp/yesterday_clusters.json"],
    destination_project_dataset_table="smaxtec_dataset.hourly_clusters",
    source_format="NEWLINE_DELIMITED_JSON",
    write_disposition="WRITE_APPEND",
    time_partitioning={"type": "DAY", "field": "hour_ts"},
    # clustering_fields removed
    gcp_conn_id="google_cloud_default",
)


    export_scaled >> train >> load_clusters
