# fake-api/app.py

from flask import Flask, jsonify
from kafka import KafkaProducer
import json
import random
import time

app = Flask(__name__)

# ------------------ Helper Functions ------------------

def bounded_random_walk(prev, lo, hi, step):
    """
    Simulate real-time variation by adding a small random step,
    staying within [lo, hi].
    """
    candidate = prev + random.uniform(-step, step)
    if candidate < lo:
        candidate = lo + (lo - candidate)
    elif candidate > hi:
        candidate = hi - (candidate - hi)
    return round(candidate, 2)

# ------------------ Persistent Cow State ------------------

STATE = {}

def get_state(cow_id):
    """Initialize or retrieve cow-specific sensor state."""
    if cow_id not in STATE:
        STATE[cow_id] = {
            "temperature": random.uniform(37.5, 38.8),
            "humidity": random.uniform(55, 75),
            "activity": random.uniform(2, 6),
            "heart_rate": random.uniform(60, 80),
            "rumination": random.uniform(30, 120),
            "milk": random.uniform(18, 28),
        }
    return STATE[cow_id]

# ------------------ Kafka Setup ------------------

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

# ------------------ Flask Endpoints ------------------

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

@app.route('/cow-data', methods=['GET'])
def send_cow_data():
    for _ in range(30000):
        cow_id = random.randint(1, 1000)
        s = get_state(cow_id)

        # Slight changes to simulate real-time behavior
        s["temperature"] = bounded_random_walk(s["temperature"], 36.0, 40.0, 0.15)
        s["humidity"] = bounded_random_walk(s["humidity"], 50.0, 80.0, 1.0)
        s["activity"] = bounded_random_walk(s["activity"], 0.0, 10.0, 0.3)
        s["heart_rate"] = int(bounded_random_walk(s["heart_rate"], 50, 100, 2))
        s["rumination"] = int(bounded_random_walk(s["rumination"], 0, 180, 5))
        s["milk"] = bounded_random_walk(s["milk"], 10.0, 30.0, 0.4)

        # Generate a valid hour_ts string (ISO format truncated to hour)
        hour_ts = time.strftime('%Y-%m-%d %H:00:00', time.gmtime(time.time()))

        fake_data = {
            "cow_id": cow_id,
            "temperature": s["temperature"],
            "humidity": s["humidity"],
            "timestamp": time.time(),
            "hour_ts": hour_ts,   # NEW: guaranteed valid timestamp string
            "activity_level": s["activity"],
            "heart_rate": s["heart_rate"],
            "rumination_minutes": s["rumination"],
            "location_x": round(random.uniform(-90.0, 90.0), 6),
            "location_y": round(random.uniform(-180.0, 180.0), 6),
            "milk_yield": s["milk"],
            "is_ruminating": random.random() < 0.4,
            "sensor_id_transformed": cow_id
        }

        # Defensive type check (optional but added for safety)
        if not isinstance(fake_data["hour_ts"], str):
            print("Invalid hour_ts detected, skipping this record")
            continue

        try:
            producer.send('sensor-data', fake_data)
            producer.flush()
        except Exception as e:
            print(f"Kafka send failed: {e}")

    print(f"Produced 30000 cow data entries.")
    return jsonify({"message": "30000 cow data sent to Kafka"})

# ------------------ Main ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
