from kafka import KafkaConsumer
import json
import time
import sys

def safe_deserializer(m):
    try:
        if m:  # Check if the message is not empty
            return json.loads(m.decode('utf-8'))  # Try to decode the message to JSON
    except json.JSONDecodeError as e:
        print(f"[Deserialization Error] Failed to decode message: {e}", flush=True)
    except Exception as e:
        print(f"[Unexpected Error] An unexpected error occurred while deserializing message: {e}", flush=True)
    return None

try:
    # Initialize Kafka Consumer
    consumer = KafkaConsumer(
        'cow-health-data',
        bootstrap_servers='kafka:9092',
        value_deserializer=safe_deserializer,  # Use the safe deserializer function
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='new-sensor-consumer-group',
        heartbeat_interval_ms=3000,
        session_timeout_ms=30000,
        max_poll_interval_ms=300000
    )
except Exception as e:
    print(f"[Startup Error] Failed to start KafkaConsumer: {e}", flush=True)
    sys.exit(1)

print("[Startup] Kafka Consumer started and listening to 'cow-health-data' topic...", flush=True)

try:
    for message in consumer:
        if message.value is not None:
            print(f"[Message Received] {json.dumps(message.value, indent=2)}", flush=True)
        else:
            print(f"[Empty Message] Received an empty message.", flush=True)
except KeyboardInterrupt:
    print("[Shutdown] Consumer shutdown requested.", flush=True)
except Exception as e:
    print(f"[Runtime Error] An error occurred while processing messages: {e}", flush=True)
finally:
    consumer.close()
    print("[Shutdown] Kafka Consumer closed.", flush=True)
