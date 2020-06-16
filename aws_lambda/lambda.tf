provider "aws" {
}

variable "function_name" {
  default = "challenge_lambda_function"
}

variable "handler" {
  default = "app.lambda_handler"
}

variable "runtime" {
  default = "python3.7"
}

variable "role_name" {
  default = "challenge_role"
}

variable "policy_name" {
  default = "challenge_policy"
}


locals {
  source_files = ["../app.py", "../config.py"]
}

data "template_file" "t_file" {
  count = "${length(local.source_files)}"

  template = "${file(element(local.source_files, count.index))}"
}

data "archive_file" "archive" {
  type        = "zip"
  output_path = "./lambda.zip"

  source {
    filename = "${basename(local.source_files[0])}"
    content  = "${data.template_file.t_file.0.rendered}"
  }

  source {
    filename = "${basename(local.source_files[1])}"
    content  = "${data.template_file.t_file.1.rendered}"
  }
}

resource "aws_iam_role" "challenge_role" {
      name = var.role_name
      path = "/"

      assume_role_policy = <<EOF
{
      "Version": "2012-10-17",
      "Statement": [
        {
          "Action": "sts:AssumeRole",
          "Principal": {
            "Service": "lambda.amazonaws.com"
          },
          "Effect": "Allow",
          "Sid": ""
        }
      ]
    }
EOF
}

resource "aws_iam_policy" "challenge_policy" {
  name = var.policy_name
  description = "Challenge policy"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
          "s3:*",
          "rds:Describe*",
          "rds:DownloadDBLogFilePortion",
          "rds:DownloadCompleteDBLogFile"
          ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:*"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "challenge-role-attach1" {
  role       = "${aws_iam_role.challenge_role.name}"
  policy_arn = "${aws_iam_policy.challenge_policy.arn}"
}

resource "aws_lambda_function" "lambda_function" {
  role = "${aws_iam_role.challenge_role.arn}"
  handler = "${var.handler}"
  runtime = "${var.runtime}"
  timeout = 900
  filename = "lambda.zip"
  function_name = "${var.function_name}"
  source_code_hash = "${data.archive_file.archive.output_base64sha256}"
}
