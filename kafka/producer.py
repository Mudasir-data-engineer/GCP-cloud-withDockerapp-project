# kafka/producer.py

from kafka import KafkaProducer
import json
import time
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Define the new fields schema
def generate_fake_cow_data():
    return {
        "cow_id": random.randint(1, 1000),
        "temperature": round(random.uniform(36.0, 40.0), 2),
        "humidity": round(random.uniform(50.0, 80.0), 2),
        "timestamp": time.time(),
        "hour_ts": time.strftime('%Y-%m-%d %H:00:00', time.gmtime(time.time())),  # <-- Added field
        "activity_level": round(random.uniform(0.0, 10.0), 2),
        "heart_rate": random.randint(50, 100),
        "rumination_minutes": random.randint(0, 180),
        "location_x": round(random.uniform(-90.0, 90.0), 6),
        "location_y": round(random.uniform(-180.0, 180.0), 6),
        "milk_yield": round(random.uniform(10.0, 30.0), 2),
        "is_ruminating": random.choice([True, False]),
        "sensor_id_transformed": random.randint(1, 1000)
    }


try:
    for i in range(3000):  # Send exactly 3000 records
        message = generate_fake_cow_data()
        producer.send('sensor-data', value=message)
        if (i + 1) % 100 == 0:
            logging.info(f"Produced {i + 1} messages")
        time.sleep(0.001)  # slight delay to avoid overwhelming Kafka

    producer.flush()
    logging.info("All 3000 messages sent and producer flushed.")
finally:
    producer.close()
    logging.info("Producer connection closed.")
