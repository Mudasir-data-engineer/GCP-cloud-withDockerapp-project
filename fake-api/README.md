# Fake API - Smaxtec Project

This service simulates an API that generates fake cow health data.

## Purpose
- Provide sample JSON data to simulate a real-world API source.
- Help Airflow and Kafka Producer to pull health data during development.

## Endpoints

| Method | Endpoint | Description |
|:------:|:---------|:-------------|
| GET | /cow-data | Returns random cow health metrics in JSON format |

## Sample JSON Output

```json
{
    "cow_id": 12,
    "temperature": 39.2,
    "heart_rate": 62,
    "activity_level": "normal",
    "rumination_time": 489,
    "timestamp": "2025-04-27T18:23:45.678Z"
}
