from kafka import KafkaConsumer
import json
import time

TOPIC_NAME = 'cow-health-data'
KAFKA_BROKER = 'kafka:9092'
GROUP_ID = 'new-sensor-consumer-group'  # match working consumer
MAX_MESSAGES = 10
POLL_TIMEOUT_MS = 5000  # timeout for poll

def safe_deserializer(m):
    try:
        if m:
            return json.loads(m.decode('utf-8'))
    except json.JSONDecodeError as e:
        print(f"[Deserialization Error] Failed to decode message: {e}", flush=True)
    except Exception as e:
        print(f"[Unexpected Error] Deserialization error: {e}", flush=True)
    return None

def wait_for_kafka():
    while True:
        try:
            consumer = KafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=KAFKA_BROKER,
                value_deserializer=safe_deserializer,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id=GROUP_ID,
                heartbeat_interval_ms=3000,
                session_timeout_ms=30000,
                max_poll_interval_ms=300000,
            )
            print("[Startup] Connected to Kafka.", flush=True)
            return consumer
        except Exception as e:
            print(f"[Wait] Kafka not ready: {e}. Retrying in 5s...", flush=True)
            time.sleep(5)

def main():
    consumer = wait_for_kafka()
    print(f"[Listening] Consuming up to {MAX_MESSAGES} messages...", flush=True)

    message_count = 0
    try:
        while message_count < MAX_MESSAGES:
            records = consumer.poll(timeout_ms=POLL_TIMEOUT_MS)
            if not records:
                print("[Timeout] No messages received. Exiting.", flush=True)
                break
            for tp, messages in records.items():
                for message in messages:
                    if message.value is not None:
                        print(f"[Message {message_count+1}] {json.dumps(message.value, indent=2)}", flush=True)
                    else:
                        print("[Empty Message] Skipped.", flush=True)
                    message_count += 1
                    if message_count >= MAX_MESSAGES:
                        break
    except Exception as e:
        print(f"[Error] While consuming: {e}", flush=True)
    finally:
        consumer.close()
        print("[Shutdown] Consumer closed.", flush=True)

if __name__ == "__main__":
    main()
