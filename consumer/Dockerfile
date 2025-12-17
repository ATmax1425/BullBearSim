FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /consumer

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "consumer_to_db.py"]
