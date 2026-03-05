provider "aws" {
  region = "us-east-1"
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "anomaly-detection-vpc"
  }
}

resource "aws_subnet" "public" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "anomaly-detection-public-${count.index}"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# MSK (Managed Streaming for Kafka) Cluster
resource "aws_msk_cluster" "kafka" {
  cluster_name           = "anomaly-detection-kafka"
  kafka_version          = "2.8.1"
  number_of_broker_nodes = 2

  broker_node_group_info {
    instance_type   = "kafka.t3.small"
    client_subnets  = aws_subnet.public[*].id
    security_groups = [aws_security_group.kafka.id]
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "PLAINTEXT"
    }
  }

  tags = {
    Environment = "production"
  }
}

resource "aws_security_group" "kafka" {
  vpc_id = aws_vpc.main.id
  
  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ECS Cluster for running containers
resource "aws_ecs_cluster" "main" {
  name = "anomaly-detection-cluster"
}

# ECR Repositories
resource "aws_ecr_repository" "producer" {
  name = "anomaly-detection/producer"
}

resource "aws_ecr_repository" "processor" {
  name = "anomaly-detection/processor"
}

resource "aws_ecr_repository" "dashboard" {
  name = "anomaly-detection/dashboard"
}

# Outputs
output "msk_bootstrap_brokers" {
  value = aws_msk_cluster.kafka.bootstrap_brokers
}
