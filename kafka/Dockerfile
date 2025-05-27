FROM python:3.11-slim

RUN pip install kafka-python

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
