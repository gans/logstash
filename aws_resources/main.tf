provider "aws" {
}

resource "aws_db_option_group" "hotmart-audit-test1" {
  name = "hotmart-audit-test1"
  option_group_description = "Hotmart audit configuration"
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
  name = "hotmart"
  username = "hotmart"
  password = "kdjuyt64gS3s2gksu"
  port = 3306
  identifier = "hotmart-test-2"
  parameter_group_name = "default.mysql5.7"
  option_group_name = "hotmart-audit-test1"
  skip_final_snapshot       = true
  final_snapshot_identifier = "Ignore"
  publicly_accessible  = true
}

resource "aws_s3_bucket" "bucket" {
    bucket                      = "hotmart-gans-s3-2"
    region                      = "us-east-2"
    request_payer               = "BucketOwner"

    versioning {
        enabled    = false
        mfa_delete = false
    }
}
