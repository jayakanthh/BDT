#!/bin/bash
# Start the EC2 instance again
INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=AnomalyDetection-Server" "Name=instance-state-name,Values=stopped" --query "Reservations[0].Instances[0].InstanceId" --output text --region us-east-1)

if [ "$INSTANCE_ID" == "None" ] || [ -z "$INSTANCE_ID" ]; then
    echo "No stopped instance found. It might be already running or terminated."
    exit 0
fi

echo "Starting EC2 Instance $INSTANCE_ID..."
aws ec2 start-instances --instance-ids $INSTANCE_ID --region us-east-1
echo "Waiting for instance to initialize..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region us-east-1

PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID --query "Reservations[0].Instances[0].PublicIpAddress" --output text --region us-east-1)

echo "Instance Started!"
echo "New Public IP: $PUBLIC_IP"
echo "Dashboard: http://$PUBLIC_IP:8501"
echo "Grafana: http://$PUBLIC_IP:3000"
echo "SSH: ssh -i terraform/deployer-key.pem ec2-user@$PUBLIC_IP"
