import time
import json
import random
import logging
import os
from datetime import datetime
from kafka import KafkaProducer
from faker import Faker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fake = Faker()

# Kafka Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
TOPIC = os.getenv('KAFKA_TOPIC', 'transactions_v2')

def create_producer():
    """Create a Kafka producer with retry logic."""
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            logger.info("Connected to Kafka!")
            return producer
        except Exception as e:
            logger.warning(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def generate_transaction():
    """Generate a synthetic transaction."""
    # Simulate normal vs anomalous data
    is_anomaly = random.random() < 0.05  # 5% chance of anomaly
    
    user_id = fake.random_int(min=1, max=1000)
    merchant_id = fake.random_int(min=1, max=500)
    
    # Velocity Simulation (Simulated as a feature for now)
    # In a real system, this would be calculated by Spark
    velocity = random.randint(1, 5)

    if is_anomaly:
        # Anomalous pattern: High amount or unusual location or High Velocity
        anomaly_type = random.choice(['amount', 'location', 'velocity'])
        
        if anomaly_type == 'amount':
            amount = round(random.uniform(5000, 50000), 2)
            location = "US"
        elif anomaly_type == 'location':
            amount = round(random.uniform(10, 1000), 2)
            location = fake.country()
        else: # velocity
            amount = round(random.uniform(10, 1000), 2)
            location = "US"
            velocity = random.randint(10, 50) # High velocity burst
            
    else:
        # Normal pattern
        amount = round(random.uniform(10, 1000), 2)
        location = "US" # Assume most transactions are US-based for this simulation
        
    return {
        'transaction_id': fake.uuid4(),
        'user_id': user_id,
        'merchant_id': merchant_id,
        'amount': amount,
        'timestamp': datetime.utcnow().isoformat(),
        'location': location,
        'velocity': velocity, # Sending this to help Spark simulation
        'is_anomaly_ground_truth': is_anomaly
    }

def main():
    producer = create_producer()
    
    logger.info(f"Starting to produce transactions to topic '{TOPIC}'...")
    
    try:
        while True:
            transaction = generate_transaction()
            producer.send(TOPIC, value=transaction)
            logger.info(f"Sent: {transaction}")
            
            # Simulate real-time data stream (variable delay)
            time.sleep(random.uniform(0.1, 1.0))
            
    except KeyboardInterrupt:
        logger.info("Stopping producer...")
    finally:
        producer.close()

if __name__ == '__main__':
    main()
