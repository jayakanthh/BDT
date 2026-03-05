FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard/ ./dashboard/

# Default command (can be overridden to run app.py or db_writer.py)
CMD ["python", "dashboard/db_writer.py"]
