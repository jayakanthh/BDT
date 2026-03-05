FROM python:3.9-slim-bullseye

WORKDIR /app

# Install Java 17 (Required for Spark)
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-arm64
# Note: On standard Linux (x86), it might be java-17-openjdk-amd64. 
# For multi-arch safety, we can rely on debian's default link, or check.
# Usually /usr/lib/jvm/default-java points to the installed version.
ENV JAVA_HOME=/usr/lib/jvm/default-java

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY processor/ ./processor/
COPY run_processor.sh .

# Ensure the script is executable
RUN chmod +x run_processor.sh

CMD ["./run_processor.sh"]