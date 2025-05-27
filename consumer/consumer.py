# consumer/consumer.py

from kafka import KafkaConsumer
import json
import sys
import time
from datetime import datetime
from google.cloud import storage
import io

TOTAL_MESSAGES = 30000
BATCH_SIZE = 3000
POLL_TIMEOUT_MS = 10_000  # 10 seconds

def safe_deserializer(m):
    try:
        if m:
            return json.loads(m.decode('utf-8'))
    except Exception as e:
        print(f"[Deserialization Error] {e}", flush=True)
    return None

def process_data(data):
    if not data or 'cow_id' not in data or 'sensor_id_transformed' not in data:
        print(f"[Invalid Data] {data}", flush=True)
        return None

    # Optional: temperature conversion safeguard
    if data.get('temperature_unit') == 'F':
        data['temperature'] = (data['temperature'] - 32) * 5.0 / 9.0
        data['temperature_unit'] = 'C'
    return data

def generate_date_time_folder():
    current_time = datetime.utcnow()
    date_str = current_time.strftime("%Y-%m-%d")
    time_str = current_time.strftime("%H-%M")
    return f"{date_str}_{time_str}"

def generate_batch_name(batch_number):
    return f"batch_{batch_number}"

def upload_to_gcs_memory(batch, date_time_str, batch_number):
    try:
        buffer = io.StringIO()
        for record in batch:
            buffer.write(json.dumps(record) + "\n")
        buffer.seek(0)

        bucket = storage.Client.from_service_account_json(
            "/opt/airflow/dags/gcs_keyfile.json"
        ).bucket("kafka-airflow-data-bucket")

        blob_path = f"cow_data/{date_time_str}/{generate_batch_name(batch_number)}.ndjson"
        blob = bucket.blob(blob_path)
        blob.upload_from_file(buffer, content_type='application/x-ndjson')
        print(f"[GCS Upload] gs://kafka-airflow-data-bucket/{blob_path}", flush=True)
    except Exception as e:
        print(f"[GCS Upload Error] {e}", flush=True)

# --- Main ---

try:
    consumer = KafkaConsumer(
        'sensor-data',
        bootstrap_servers='kafka:9092',
        value_deserializer=safe_deserializer,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='sensor-consumer-gcs-group',
        heartbeat_interval_ms=3000,
        session_timeout_ms=30000,
        max_poll_interval_ms=300000
    )
    print("[Startup] Kafka Consumer ready.", flush=True)
except Exception as e:
    print(f"[Startup Error] {e}", flush=True)
    sys.exit(1)

collected = []
count = 0
batch_number = 1

try:
    while count < TOTAL_MESSAGES:
        print("[Polling] Waiting for messages...", flush=True)
        msg_pack = consumer.poll(timeout_ms=POLL_TIMEOUT_MS)
        if not msg_pack:
            print("[Timeout] No messages in last 10s.", flush=True)
            break

        for tp, msgs in msg_pack.items():
            for m in msgs:
                rec = process_data(m.value)
                if rec:
                    collected.append(rec)
                    count += 1
                if len(collected) >= BATCH_SIZE:
                    date_time_str = generate_date_time_folder()
                    upload_to_gcs_memory(collected, date_time_str, batch_number)
                    collected = []
                    batch_number += 1
                if count >= TOTAL_MESSAGES:
                    break

except KeyboardInterrupt:
    print("[Shutdown] Interrupted by user.", flush=True)
except Exception as e:
    print(f"[Runtime Error] {e}", flush=True)
finally:
    if collected:
        date_time_str = generate_date_time_folder()
        upload_to_gcs_memory(collected, date_time_str, batch_number)
    consumer.close()
    print(f"[Shutdown] Consumer closed. Total processed: {count}", flush=True)
