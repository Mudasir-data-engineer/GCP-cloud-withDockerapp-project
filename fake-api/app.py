from flask import Flask, jsonify
from kafka import KafkaProducer
import json
import random
import time
import socket

app = Flask(__name__)

# Retry Kafka producer creation
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
    fake_data = {
        "cow_id": random.randint(1, 1000),
        "temperature": round(random.uniform(36.0, 40.0), 2),
        "humidity": round(random.uniform(50.0, 80.0), 2),
        "timestamp": time.time()
    }
    try:
        producer.send('sensor-data', fake_data)
        producer.flush()
    except Exception as e:
        print(f"Kafka send failed: {e}")

    print(f"Produced cow data: {fake_data}")
    return jsonify({"message": "Cow data sent to Kafka", "data": fake_data})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
