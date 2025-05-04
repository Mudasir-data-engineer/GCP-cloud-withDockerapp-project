# kafka/producer.py

from kafka import KafkaProducer
import json
import time

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Send a few messages and exit (so Airflow doesn’t hang forever)
for _ in range(3):
    message = {"cow_id": 123, "temperature": 38.5}
    producer.send('cow-data', value=message)
    print(f"Produced message: {message}")
    time.sleep(1)

producer.flush()
producer.close()
