from kafka import KafkaConsumer
import json
import time

TOPIC_NAME = 'sensor-data'
KAFKA_BROKER = 'kafka:9092'

# Wait until Kafka is available
def wait_for_kafka():
    while True:
        try:
            consumer = KafkaConsumer(
                TOPIC_NAME,
                bootstrap_servers=KAFKA_BROKER,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='cow-consumer-group',  # ✅ important addition
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            print("Connected to Kafka.")
            return consumer
        except Exception as e:
            print(f"Kafka not available yet: {e}. Retrying in 5 seconds...")
            time.sleep(5)

consumer = wait_for_kafka()

print("Consumer is listening for messages...")  # ✅ good feedback

for message in consumer:
    print(f"Received message: {message.value}")
