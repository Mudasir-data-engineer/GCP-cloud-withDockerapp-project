from airflow.providers.google.cloud.hooks.gcs import GCSHook
import os

# Configuration
BUCKET_NAME = 'smaxtec-project-bucket'
SOURCE_PREFIX = 'cow_data/'
PROCESSED_PREFIX = 'cow_data/processed_folders/'
GCP_CONN_ID = 'google_cloud_default'
KEY_FILE = os.path.join(os.path.dirname(__file__), 'gcs_keyfile.json')

def move_existing_folders_to_processed():
    hook = GCSHook(gcp_conn_id=GCP_CONN_ID)
    all_blobs = hook.list(bucket_name=BUCKET_NAME, prefix=SOURCE_PREFIX)

    # Ignore already processed or irrelevant files
    for blob in all_blobs:
        parts = blob.split('/')
        if len(parts) >= 2:
            folder_name = parts[1]
            if folder_name == 'processed_folders' or not folder_name:
                continue  # skip

            # Compute new destination
            dest_blob = f"{PROCESSED_PREFIX}{folder_name}/" + '/'.join(parts[2:])
            print(f"Moving: {blob} → {dest_blob}")

            # Copy
            hook.copy(
                source_bucket=BUCKET_NAME,
                source_object=blob,
                destination_bucket=BUCKET_NAME,
                destination_object=dest_blob
            )

            # Delete original
            hook.delete(bucket_name=BUCKET_NAME, object_name=blob)

    print("✅ All existing folders moved to processed_folders.")

# Run this function manually when needed
if __name__ == "__main__":
    move_existing_folders_to_processed()
