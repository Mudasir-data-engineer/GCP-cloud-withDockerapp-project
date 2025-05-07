# consumer/Dockerfile

FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip show kafka-python

COPY . .

CMD ["python", "consumer.py"]
