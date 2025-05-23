import argparse
import json
import os
import tempfile

import pandas as pd
from google.cloud import storage
from joblib import load, dump
from sklearn.preprocessing import StandardScaler

bucket_name = "kafka-airflow-data-bucket"
project_id = "kafka-airflow-data-project"

def download_blob(gcs_path: str, local_path: str):
    bucket_name, blob_path = gcs_path.replace("gs://", "").split("/", 1)
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.download_to_filename(local_path)

def upload_blob(local_path: str, gcs_path: str):
    bucket_name, blob_path = gcs_path.replace("gs://", "").split("/", 1)
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(local_path)

def check_blob_exists(gcs_path: str) -> bool:
    bucket_name, blob_path = gcs_path.replace("gs://", "").split("/", 1)
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    return blob.exists()

def train_and_upload_scaler(df: pd.DataFrame, gcs_path: str, local_path: str):
    print("⚠️ Scaler not found. Training a new scaler...")
    meta_cols = ["hour_ts", "is_ruminating"]
    feature_cols = [col for col in df.columns if col not in meta_cols]
    train_data = df[feature_cols]

    scaler = StandardScaler()
    scaler.fit(train_data)

    dump(scaler, local_path)
    upload_blob(local_path, gcs_path)
    print(f"✅ Trained and uploaded new scaler to {gcs_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input JSON file on GCS")
    parser.add_argument("--output", required=True, help="Output path on GCS")
    parser.add_argument("--scaler", required=True, help="Pre-fitted scaler on GCS")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp_dir:
        local_input = os.path.join(tmp_dir, "input.json")
        local_output = os.path.join(tmp_dir, "output.json")
        local_scaler = os.path.join(tmp_dir, "scaler.joblib")

        try:
            download_blob(args.input, local_input)
        except Exception as e:
            raise RuntimeError(f"❌ Failed to download input: {e}")

        df = pd.read_json(local_input, lines=True)

        if not check_blob_exists(args.scaler):
            train_and_upload_scaler(df, args.scaler, local_scaler)
        else:
            download_blob(args.scaler, local_scaler)

        meta_cols = ["hour_ts", "is_ruminating"]
        feature_cols = [col for col in df.columns if col not in meta_cols]

        scaler = load(local_scaler)
        scaled = scaler.transform(df[feature_cols])
        scaled_df = pd.DataFrame(scaled, columns=feature_cols)

        final_df = pd.concat([df[meta_cols].reset_index(drop=True), scaled_df], axis=1)

        final_df.to_json(local_output, orient="records", lines=True)

        try:
            upload_blob(local_output, args.output)
        except Exception as e:
            raise RuntimeError(f"❌ Failed to upload output: {e}")

        print(f"✅ Successfully scaled data and saved to {args.output}")

if __name__ == "__main__":
    main()
