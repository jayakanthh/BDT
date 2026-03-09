#!/bin/bash
set -e

# Check for Terraform
if ! command -v terraform &> /dev/null; then
    echo "Error: Terraform is not installed. Please install it first."
    echo "Brew: brew install terraform"
    exit 1
fi

# Check for AWS Credentials
if [ ! -d "$HOME/.aws" ] && [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "Error: AWS credentials not found. Please run 'aws configure' or set environment variables."
    exit 1
fi

echo "Initializing Terraform..."
cd terraform
terraform init

echo "Applying Terraform configuration..."
# Auto-approve to make it smoother, but warn user
echo "This will create a t2.micro EC2 instance (Free Tier eligible) in us-east-1."
read -p "Do you want to proceed? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

terraform apply -auto-approve

echo ""
echo "Deployment initiated!"
echo "---------------------------------------------------"
echo "Note: It may take 5-10 minutes for the instance to initialize,"
echo "install Docker, and start the containers."
echo ""
echo "Access Details:"
terraform output
echo ""
echo "To SSH into the instance:"
echo "$(terraform output -raw ssh_connection_string)"
echo ""
echo "To destroy resources later (avoid costs):"
echo "cd terraform && terraform destroy"
