variable "audit_id" {
  type = string
  default = "challenge-audit-test1"
}

variable "rds_id" {
  type = string
  default = "challengerds1"
}

variable "rds_name" {
  type = string
  default  = "challenge1"
}

variable "rds_username" {
  type = string
  default = "hotmart"
}

variable "rds_password" {
  type = string
  default = "kdjuyt64gS3s2gksu"
}

variable "s3_bucket" {
  type = string
  default = "challengebucket1"
}

variable "aws_region" {
  type = string
  default = "us-east-2"
}

provider "aws" {
}

resource "aws_db_option_group" "challenge-audit-test1" {
  name = var.audit_id
  option_group_description = "Challenge audit configuration"
  engine_name = "mysql"
  major_engine_version = "5.7"

  option {
    option_name = "MARIADB_AUDIT_PLUGIN"

    option_settings {
      name = "SERVER_AUDIT_EXCL_USERS"
      value = "rdsadmin"
    }
    option_settings {
      name = "SERVER_AUDIT_FILE_ROTATIONS"
      value = "15"
    }
    option_settings {
      name = "SERVER_AUDIT_FILE_ROTATE_SIZE"
      value = "100000"
    }
  }
}

resource "aws_db_instance" "main" {
  allocated_storage = 20
  storage_type = "gp2"
  engine = "mysql"
  engine_version = "5.7.28"
  instance_class = "db.t2.micro"
  name = var.rds_name
  username = var.rds_username
  password = var.rds_password
  port = 3306
  identifier = var.rds_id
  parameter_group_name = "default.mysql5.7"
  option_group_name = var.audit_id
  skip_final_snapshot = true
  final_snapshot_identifier = "Ignore"
  publicly_accessible  = true
}

output "rds_endpoint" {
  value = "${aws_db_instance.main.endpoint}"
}

resource "aws_s3_bucket" "bucket" {
    bucket = var.s3_bucket
    region = var.aws_region
    request_payer = "BucketOwner"

    versioning {
        enabled    = false
        mfa_delete = false
    }
}

