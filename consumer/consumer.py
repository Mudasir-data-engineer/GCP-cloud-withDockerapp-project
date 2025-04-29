from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'sensor-data',
    bootstrap_servers='kafka:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='sensor-consumer-group'
)

print("Kafka Consumer started and listening to 'sensor-data' topic...")

for message in consumer:
    print(f"Received message: {message.value}")
