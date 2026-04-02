provider "aws" {
  region = "us-east-1"
}

# --- VPC & Networking ---
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "anomaly-detection-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-east-1a"
  
  tags = {
    Name = "anomaly-detection-public"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# --- Security Group ---
resource "aws_security_group" "app_sg" {
  name        = "anomaly-detection-sg"
  description = "Allow inbound traffic for SSH and dashboard apps"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Streamlit
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Grafana
  }
  
  ingress {
    from_port   = 8888
    to_port     = 8888
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Chronograf
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- AMI Data Source ---
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# --- EC2 Instance (Free Tier Eligible) ---
resource "aws_instance" "app_server" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  key_name      = aws_key_pair.deployer.key_name
  
  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = <<-EOF
              #!/bin/bash
              # Update system
              yum update -y
              
              # Install Git
              yum install -y git
              
              # Install Docker
              amazon-linux-extras install docker -y
              service docker start
              usermod -a -G docker ec2-user
              
              # Install Docker Compose
              curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose
              
              # Setup Swap (Critical for t2.micro with 1GB RAM)
              dd if=/dev/zero of=/swapfile bs=1M count=2048
              chmod 600 /swapfile
              mkswap /swapfile
              swapon /swapfile
              echo "/swapfile swap swap defaults 0 0" >> /etc/fstab
              
              # Clone Repository
              cd /home/ec2-user
              git clone https://github.com/jayakanthh/BDT.git
              chown -R ec2-user:ec2-user BDT
              
              # Start Application
              cd BDT/realtime-anomaly-detection
              # We need to run as ec2-user or ensure docker permissions
              # Using runuser to run as ec2-user for proper file ownership
              # Also, ensure we build the images locally since we're not pulling from ECR in this setup
              /usr/local/bin/docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
              EOF

  tags = {
    Name = "AnomalyDetection-Server"
  }
}

# --- Key Pair ---
# Generates a new key pair. In production, you'd likely import a public key.
resource "tls_private_key" "pk" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "deployer" {
  key_name   = "deployer-key"
  public_key = tls_private_key.pk.public_key_openssh
}

resource "local_file" "ssh_key" {
  content  = tls_private_key.pk.private_key_pem
  filename = "${path.module}/deployer-key.pem"
  file_permission = "0400"
}

# --- Outputs ---
output "instance_public_ip" {
  value = aws_instance.app_server.public_ip
}

output "ssh_connection_string" {
  value = "ssh -i deployer-key.pem ec2-user@${aws_instance.app_server.public_ip}"
}

output "dashboard_url" {
  value = "http://${aws_instance.app_server.public_ip}:8501"
}

output "grafana_url" {
  value = "http://${aws_instance.app_server.public_ip}:3000"
}
