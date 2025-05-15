# Smaxtec Data Ingestion Pipeline

This project automates the ingestion, processing, and storage of cow sensor data using Apache Airflow, Kafka, and Google Cloud Platform (GCS + BigQuery). It consists of two main Airflow DAGs and a one-time manual cleanup script.

---

## Project Overview

The system operates in two key stages:

1. **Data Generation and Processing**  
   Simulates data ingestion using Kafka and a fake API, then stores raw data in Google Cloud Storage (GCS).

2. **Data Loading and Organizing**  
   Loads processed data from GCS into BigQuery and organizes processed files in GCS.

Additionally, a one-time script is provided to organize existing data before automation begins.

---

## DAG 1: `smaxtec_dag.py`

### Purpose  
Simulates real-time sensor data ingestion and processing.

### How it works  
- Runs **every 3 hours** to simulate ongoing data ingestion.  
- Performs a **health check** on the fake API before proceeding.  
- Calls the **fake API** to fetch cow sensor data.  
- Runs a **Kafka producer** to send data to Kafka topics.  
- Runs a **pipeline processor (consumer)** to process Kafka messages and store results in GCS under `cow_data/`.

### Schedule  

---

## DAG 2: `bigquery_dag.py`

### Purpose  
Automates loading of processed data from GCS into BigQuery and moves processed data to a separate folder.

### How it works  
- Runs **twice daily** at midnight and noon.  
- Lists all **unprocessed folders** in GCS under `cow_data/`.  
- For each folder:  
  - Loads up to 10 `.ndjson` files into the BigQuery table `smaxtec_dataset.smaxtec_data`.  
  - Moves the processed folder to `cow_data/processed_folders/` in GCS to avoid reprocessing.

### Schedule  

---

## One-time Manual Script: `gcs_moved_to_processed.py`

### Purpose  
Initial cleanup script to move existing data folders in GCS from `cow_data/` to `cow_data/processed_folders/`.

### How it works  
- Scans all files under `cow_data/` in GCS.  
- Skips the `processed_folders` directory itself.  
- Moves all other folders and their contents to the `processed_folders/` location.  
- **Run manually only once** before enabling the BigQuery ingestion DAG, to avoid reprocessing old data. #python gcs_move_to_processed.py

---

## Usage Notes

- Ensure service account keys and GCP connections are properly configured in Airflow.  
- Adjust scheduling times as needed for your workload.  
- Run the one-time manual script before starting the BigQuery ingestion DAG to keep the workflow clean.

---
