#!/bin/bash

# Check if SPARK_HOME is set (optional, spark-submit might be in PATH)
if ! command -v spark-submit &> /dev/null; then
    echo "Error: spark-submit could not be found. Please ensure Apache Spark is installed and in your PATH."
    exit 1
fi

echo "Submitting Spark Job..."

# Force Java 17 if available (Spark has issues with Java 21+)
if [ -d "/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home" ]; then
    export JAVA_HOME="/opt/homebrew/Cellar/openjdk@17/17.0.17/libexec/openjdk.jdk/Contents/Home"
    echo "Using Java 17 at $JAVA_HOME"
elif [ -x "/usr/libexec/java_home" ]; then
    # Try to find Java 17 dynamically
    JAVA17=$(/usr/libexec/java_home -v 17 2>/dev/null)
    if [ ! -z "$JAVA17" ]; then
        export JAVA_HOME="$JAVA17"
        echo "Using Java 17 at $JAVA_HOME"
    fi
fi

while true; do
    # Run the Spark Streaming Job
    # Using local[*] to run locally with all cores
    # Including the Kafka dependency for Spark Structured Streaming
    spark-submit \
        --master local[*] \
        --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
        --conf spark.driver.extraJavaOptions="-Djava.net.preferIPv4Stack=true" \
        --conf spark.executor.extraJavaOptions="-Djava.net.preferIPv4Stack=true" \
        processor/spark_job.py
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Spark job finished successfully."
        break
    else
        echo "Spark job failed (likely Kafka not ready). Retrying in 10 seconds..."
        sleep 10
    fi
done
