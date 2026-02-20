# Real-Time Anomaly Detection System (Enterprise Edition)

This project implements an end-to-end real-time anomaly detection pipeline for financial transactions using a modern, enterprise-grade technology stack.

## 🏗 Architecture

The system follows a microservices architecture:

1.  **Producer (Python)**: Generates synthetic transaction data (95% normal, 5% anomalous).
2.  **Message Broker (Kafka)**: Handles high-throughput data ingestion and decoupling.
3.  **Stream Processing (PySpark)**: Consumes data from Kafka, applies an Isolation Forest machine learning model to detect anomalies in real-time, and writes results back to Kafka.
4.  **Data Collection (Telegraf)**: A lightweight agent that consumes the processed results from Kafka and forwards them to the time-series database.
5.  **Storage (InfluxDB)**: A high-performance time-series database optimized for metrics and events.
6.  **Visualization (Grafana)**: A powerful dashboarding tool for monitoring transaction volume, anomaly rates, and real-time alerts.
7.  **Management (Chronograf)**: Admin interface for InfluxDB.

## 🚀 Tech Stack

*   **Kafka & Zookeeper**: Event Streaming Platform
*   **PySpark**: Distributed Stream Processing
*   **InfluxDB**: Time-Series Database
*   **Telegraf**: Server Agent for Collecting & Reporting Metrics
*   **Grafana**: Analytics & Monitoring Solution
*   **Chronograf**: The user interface and administrative component of the InfluxData platform
*   **Python**: Data generation and ML logic

## 🛠 Setup & Running

### Prerequisites
*   Docker & Docker Compose
*   Python 3.9+ (for local producer/processor execution)

### 1. Start the Infrastructure
Spin up the entire containerized environment:
```bash
docker-compose up -d
```
This starts Kafka, Zookeeper, InfluxDB, Telegraf, Grafana, and Chronograf.

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Data Pipeline
Open two terminal windows:

**Terminal 1: Start the Transaction Producer**
```bash
python3 producer/main.py
```

**Terminal 2: Start the Spark Processor**
```bash
./run_processor.sh
```

## 📊 Dashboards

### Grafana (Visualization)
*   **URL**: [http://localhost:3000](http://localhost:3000)
*   **Credentials**: `admin` / `admin`
*   **Setup**:
    1.  Log in.
    2.  Add Data Source -> InfluxDB.
    3.  URL: `http://influxdb:8086`, Database: `anomaly_detection`.
    4.  Import Dashboard (or create a new one querying the `transactions` measurement).

### Chronograf (DB Admin)
*   **URL**: [http://localhost:8888](http://localhost:8888)
*   **Use**: Explore data, manage InfluxDB users and retention policies.

## 📈 Data Flow
1.  `producer/main.py` -> **Kafka Topic**: `transactions`
2.  `processor/spark_job.py` -> **Kafka Topic**: `anomalies` (JSON format with `prediction` field)
3.  `telegraf` -> Consumes `anomalies` topic -> Writes to **InfluxDB** `anomaly_detection` DB
4.  `grafana` -> Queries **InfluxDB** -> Displays Real-Time Graphs

## 🛑 Stopping
```bash
docker-compose down
# Or to remove volumes (reset data):
docker-compose down -v
```
