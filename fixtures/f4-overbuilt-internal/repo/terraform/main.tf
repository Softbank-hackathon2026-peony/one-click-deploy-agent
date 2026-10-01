provider "aws" {
  region = "ap-northeast-2"
}

provider "aws" {
  alias  = "us"
  region = "us-east-1"
}

resource "aws_eks_cluster" "main" {
  name     = "internal"
  role_arn = "arn:aws:iam::123456789012:role/eks"
  vpc_config {
    subnet_ids = ["subnet-a", "subnet-b", "subnet-c"]
  }
}

resource "aws_nat_gateway" "a" {
  subnet_id = "subnet-a"
}

resource "aws_nat_gateway" "b" {
  subnet_id = "subnet-b"
}

resource "aws_nat_gateway" "c" {
  subnet_id = "subnet-c"
}

resource "aws_db_instance" "main" {
  engine                  = "postgres"
  instance_class          = "db.r6g.large"
  multi_az                = true
  backup_retention_period = 7
}

resource "aws_db_instance" "replica_us" {
  provider            = aws.us
  replicate_source_db = "main"
  instance_class      = "db.r6g.large"
}
