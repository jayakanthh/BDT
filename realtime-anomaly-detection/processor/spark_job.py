import logging
import sys
import json
import random
import os
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf, struct, hour, to_timestamp, lit, window, avg, stddev, count
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType, BooleanType
from sklearn.ensemble import IsolationForest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
INPUT_TOPIC = os.getenv('INPUT_TOPIC', 'transactions_v2')
OUTPUT_TOPIC = os.getenv('OUTPUT_TOPIC', 'anomalies_v2')
CHECKPOINT_DIR = os.getenv('CHECKPOINT_DIR', '/tmp/spark_checkpoint_kafka_v2')

# Schema for incoming data
schema = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("user_id", IntegerType(), True),
    StructField("merchant_id", IntegerType(), True),
    StructField("amount", DoubleType(), True),
    StructField("timestamp", StringType(), True),
    StructField("location", StringType(), True),
    StructField("is_anomaly_ground_truth", BooleanType(), True)
])

def train_isolation_forest():
    """
    Train a simple Isolation Forest model on synthetic normal data.
    In a real scenario, you'd load a pre-trained model or train on historical data.
    """
    logger.info("Training Isolation Forest model on synthetic data...")
    # Generate synthetic "normal" data for training
    # Normal behavior: Low amounts, US location
    X_train = []
    for _ in range(1000):
        amount = random.uniform(10, 1000)
        is_foreign = 0 # Mostly US
        velocity = random.uniform(0, 5) # Normal velocity
        X_train.append([amount, is_foreign, velocity])
    
    # Add a few anomalies to make it robust
    for _ in range(50):
        amount = random.uniform(5000, 50000)
        is_foreign = 1
        velocity = random.uniform(10, 50) # High velocity
        X_train.append([amount, is_foreign, velocity])
        
    clf = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    clf.fit(X_train)
    logger.info("Model trained successfully.")
    return clf

def main():
    # Initialize Spark Session
    # Note: We need to include the Kafka package when submitting the job
    spark = SparkSession.builder \
        .appName("RealTimeAnomalyDetection") \
        .config("spark.sql.shuffle.partitions", "2") \
        .config("spark.driver.host", "127.0.0.1") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.ui.enabled", "false") \
        .config("spark.network.timeout", "600s") \
        .config("spark.hadoop.ipc.client.connect.max.retries", "10") \
        .config("spark.hadoop.ipc.client.connect.retry.interval", "1000") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
        .config("spark.hadoop.fs.defaultFS", "file:///") \
        .master("local[*]") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Train Model
    clf = train_isolation_forest()
    
    # Broadcast the model to executors (essential for performance/serialization)
    broadcast_clf = spark.sparkContext.broadcast(clf)

    # Define UDF to apply the model
    @udf(returnType=StringType())
    def predict_anomaly(amount, location, velocity):
        # Feature Engineering inside UDF
        is_foreign = 1 if location != 'US' else 0
        # Use velocity as a feature
        features = [[amount, is_foreign, velocity]]
        
        model = broadcast_clf.value
        prediction = model.predict(features)[0] # 1 for normal, -1 for anomaly
        return "Anomaly" if prediction == -1 else "Normal"

    # Read from Kafka
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", INPUT_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    # Schema for incoming data (Updated with velocity)
    schema = StructType([
        StructField("transaction_id", StringType(), True),
        StructField("user_id", IntegerType(), True),
        StructField("merchant_id", IntegerType(), True),
        StructField("amount", DoubleType(), True),
        StructField("timestamp", StringType(), True),
        StructField("location", StringType(), True),
        StructField("velocity", IntegerType(), True), # Added from producer
        StructField("is_anomaly_ground_truth", BooleanType(), True)
    ])

    # Parse JSON
    parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

    # Add Timestamp column
    processed_df = parsed_df \
        .withColumn("timestamp_dt", to_timestamp(col("timestamp")))

    # Apply Prediction (Using velocity from producer directly for better accuracy)
    final_df = processed_df \
        .withColumn("prediction", predict_anomaly(col("amount"), col("location"), col("velocity")))

    # Filter for Anomalies (or just output everything with the prediction)
    # Let's output everything so the dashboard can show stats
    output_df = final_df.select(
        col("transaction_id"),
        col("amount"),
        col("location"),
        col("velocity"),
        col("prediction"),
        col("timestamp"),
        col("is_anomaly_ground_truth") # For verification
    )

    # Write to Kafka (Sink)
    # We need to serialize the output as JSON
    kafka_query = output_df.selectExpr("to_json(struct(*)) AS value") \
        .writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("topic", OUTPUT_TOPIC) \
        .option("checkpointLocation", CHECKPOINT_DIR) \
        .outputMode("append") \
        .start()

    # Also write to Console for debugging
    # console_query = output_df.writeStream \
    #     .outputMode("append") \
    #     .format("console") \
    #     .option("checkpointLocation", "/tmp/spark_checkpoint_console_" + str(random.randint(0, 100000))) \
    #     .start()

    logger.info("Streaming job started...")
    kafka_query.awaitTermination()
    # console_query.awaitTermination()

if __name__ == "__main__":
    main()
