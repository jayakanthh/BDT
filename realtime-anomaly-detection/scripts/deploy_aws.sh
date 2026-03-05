#!/bin/bash
set -e

# Load AWS credentials from local .aws directory if present
if [ -d ".aws" ]; then
    export AWS_SHARED_CREDENTIALS_FILE=$(pwd)/.aws/credentials
    export AWS_CONFIG_FILE=$(pwd)/.aws/config
fi

# Configuration
AWS_REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

echo "Building and pushing Producer..."
docker build -t ${ECR_URI}/anomaly-detection/producer:latest -f producer/Dockerfile .
docker push ${ECR_URI}/anomaly-detection/producer:latest

echo "Building and pushing Processor..."
docker build -t ${ECR_URI}/anomaly-detection/processor:latest -f processor/Dockerfile .
docker push ${ECR_URI}/anomaly-detection/processor:latest

echo "Building and pushing Dashboard..."
docker build -t ${ECR_URI}/anomaly-detection/dashboard:latest -f dashboard/Dockerfile .
docker push ${ECR_URI}/anomaly-detection/dashboard:latest

echo "Deployment images pushed successfully!"
