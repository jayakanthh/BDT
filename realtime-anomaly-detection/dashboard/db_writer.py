import json
import sqlite3
import logging
import time
from datetime import datetime
from kafka import KafkaConsumer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Alert Configuration (Simulated for MVP)
# In production, this would use AWS SNS, Slack Webhook, or PagerDuty
def send_alert(transaction):
    """Send an alert for a high-confidence anomaly."""
    msg = f"🚨 HIGH SEVERITY ALERT: Anomaly Detected! ID: {transaction['transaction_id']}, Amount: ${transaction['amount']}, Location: {transaction['location']}, Velocity: {transaction.get('velocity', 'N/A')}"
    logger.warning(msg)
    # Simulate sending to an external system by appending to a log file
    with open("alerts.log", "a") as f:
        f.write(f"{datetime.utcnow().isoformat()} - {msg}\n")

import os
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TOPIC = os.getenv('KAFKA_TOPIC', 'anomalies_v2')
DB_PATH = os.getenv('DB_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'anomalies.db'))
print(f"DB Path: {DB_PATH}")

# Initialize SQLite DB
def init_db():
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS anomalies
                     (transaction_id TEXT PRIMARY KEY, 
                      amount REAL, 
                      location TEXT, 
                      velocity INTEGER,
                      timestamp TEXT, 
                      is_anomaly_ground_truth BOOLEAN,
                      prediction TEXT)''')
        conn.commit()
        conn.close()
        logging.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")

# Save to SQLite
def save_to_db(transaction):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''INSERT OR IGNORE INTO anomalies 
                     (transaction_id, amount, location, velocity, timestamp, is_anomaly_ground_truth, prediction)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                  (transaction['transaction_id'], 
                   transaction['amount'], 
                   transaction['location'],
                   transaction.get('velocity', 0),
                   transaction['timestamp'], 
                   transaction['is_anomaly_ground_truth'], 
                   transaction.get('prediction', 'Unknown')))
        conn.commit()
        conn.close()
        # logging.info(f"Saved: {transaction['transaction_id']}")
    except Exception as e:
        logging.error(f"Error saving to DB: {e}")

def main():
    init_db()
    
    logger.info(f"Listening to topic '{TOPIC}' and writing to '{DB_PATH}'...")
    
    consumer = None
    while True:
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='earliest'
            )
            logger.info("Connected to Kafka!")
            break
        except Exception as e:
            logger.warning(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")
            time.sleep(5)
    
    try:
        for message in consumer:
            transaction = message.value
            logging.info(f"Received: {transaction}")
            save_to_db(transaction)
            
            # Check for high-confidence anomalies to alert
            # Logic: If it's an anomaly AND (Amount > 10000 OR Velocity > 10)
            if transaction.get('prediction') == 'Anomaly':
                amount = float(transaction.get('amount', 0))
                velocity = int(transaction.get('velocity', 0))
                
                if amount > 10000 or velocity > 10:
                    send_alert(transaction)
            
    except KeyboardInterrupt:
        logging.info("Stopping DB Writer...")

if __name__ == "__main__":
    main()
