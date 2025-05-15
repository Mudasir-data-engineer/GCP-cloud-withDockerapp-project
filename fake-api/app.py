# fake-api/app.py

from flask import Flask, jsonify
from kafka import KafkaProducer
import json
import random
import time

app = Flask(__name__)

# Define the new fields schema
FIELDS = [
    "temperature", "humidity", "timestamp", "activity_level", "heart_rate", 
    "rumination_minutes", "location_x", "location_y", "milk_yield", "is_ruminating", 
    "sensor_id_transformed"
]

def create_producer():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Kafka Producer created successfully.")
            return producer
        except Exception as e:
            print(f"Kafka connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

producer = create_producer()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

@app.route('/cow-data', methods=['GET'])
def send_cow_data():
    # Generate 3000 cow data records with the new fields
    for _ in range(3000):
        fake_data = {
            "cow_id": random.randint(1, 1000),
            "temperature": round(random.uniform(36.0, 40.0), 2),
            "humidity": round(random.uniform(50.0, 80.0), 2),
            "timestamp": time.time(),
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
            producer.send('sensor-data', fake_data)
            producer.flush()
        except Exception as e:
            print(f"Kafka send failed: {e}")

    print(f"Produced 3000 cow data entries.")
    return jsonify({"message": "3000 cow data sent to Kafka"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
