#!/bin/bash
# Stop the EC2 instance to save costs without destroying data
INSTANCE_ID=$(cd terraform && terraform output -raw instance_id 2>/dev/null)

if [ -z "$INSTANCE_ID" ]; then
    # Fallback to finding by tag if terraform output isn't available
    INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=AnomalyDetection-Server" "Name=instance-state-name,Values=running" --query "Reservations[0].Instances[0].InstanceId" --output text --region us-east-1)
fi

if [ "$INSTANCE_ID" == "None" ] || [ -z "$INSTANCE_ID" ]; then
    echo "No running instance found."
    exit 0
fi

echo "Stopping EC2 Instance $INSTANCE_ID..."
aws ec2 stop-instances --instance-ids $INSTANCE_ID --region us-east-1
echo "Instance stopping. You will not be billed for compute hours while stopped."
echo "Storage (EBS) costs still apply."
