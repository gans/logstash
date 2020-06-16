#encoding: utf-8
import os
import boto3, botocore
import json
import datetime
import logging
import sys
import config


S3_CONFIG_FILE = "s3_config.json"

class App:

    def __init__(self, rds_client, s3_client, debug=False):

        self.rds_client = rds_client
        self.s3_client = s3_client

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        if debug:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
                
        self.logger.info("start retrivieng rds log")

        
        self.last_written = self.get_last_s3_written()
        self.logger.info("last s3 written is {}".format(self.last_written))
        logs_desc = self.get_logs_metadata()
        if logs_desc:
            logs_desc = self.sort_last_first(logs_desc)
            self.logger.info("found logs to download, initializing")
            self.save_last_written(logs_desc)
            self.download_log(logs_desc)
        else:
            self.logger.info("not found logs to download, ending")
            
        self.logger.info("ending retrieving rds logs")

    def get_last_s3_written(self):
        try:
            response = self.s3_client.head_bucket(Bucket=config.aws_bucket_instance)
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response['ResponseMetadata']['HTTPStatusCode'])
            if error_code == 404:
                raise botocore.exceptions.ClientError("Error: Bucket name provided not found")
            else:
                botocore.exceptions.ClientError("Error: Unable to access bucket name, error: {}".format(
                            e.response["Error"]["Message"]))

        try:
            response = self.s3_client.get_object(Bucket=config.aws_bucket_instance, Key=S3_CONFIG_FILE)
            j = response["Body"].read(response["ContentLength"])
            j = json.loads(j)
            self.logger.info("config file was sucessfull written on s3")
            return j["LastWritten"] + 1
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response["ResponseMetadata"]["HTTPStatusCode"])
            if error_code == 404:
                self.logger.info("config file was not found, using default for first time")
                return 0
            else:
                raise botocore.exceptions.ClientError("Error: Unable to access the config file {}".format(
                            e.response["Error"]["Message"]))


    def get_logs_metadata(self):
        marker = ""
        more_logs = True
        logs = []
    
        while more_logs:
            response = self.rds_client.describe_db_log_files(
                DBInstanceIdentifier=config.aws_rds_instance,
                FilenameContains="server_audit.log.",
                FileLastWritten=self.last_written,
                Marker=marker
                )
            if response.get("Marker", "") != "":
                marker = response["Marker"]
            else:
                more_logs = False

            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                logs += response["DescribeDBLogFiles"]

        return logs


    def sort_last_first(self, logs_desc):
        return sorted(logs_desc, key=lambda x: x["LastWritten"])


    def save_last_written(self, logs_desc):

        last = logs_desc[-1]
        try:
            response = self.s3_client.put_object(Bucket=config.aws_bucket_instance,
                                                Key=S3_CONFIG_FILE,
                                                Body=json.dumps(last))
        except botocore.exceptions.ClientError as e:
            self.logger.error("could not write config file on s3: {}".format(
                    e.response["Error"]["Message"]))
            raise botocore.exceptions.ClientError("Error: could not save config file on s3 {}".format(
                                e.response["Error"]["Message"]))


    def download_log(self, logs):

        file_data = ""
        last_written = {"LastWritten":0}

        dwl = lambda p1, p2, p3: self.rds_client.download_db_log_file_portion(
                                DBInstanceIdentifier=p1,
                                LogFileName=p2,
                                Marker=p3)

        for log in logs:
            id_file_log = "audit-{}.log".format(
                            datetime.datetime.fromtimestamp(
                                log["LastWritten"]/1000).isoformat())
            self.logger.info("downloading {}".format(id_file_log))

            mpu_id = self.create_s3_mpu(id_file_log)
            parts = []
            uploaded_bytes = 0
            i = 1

            log_file = dwl(config.aws_rds_instance, log["LogFileName"], "0")
            log_file_data = log_file["LogFileData"]

            part = self.upload_s3_part(
                                    log_file_data,
                                    id_file_log,
                                    mpu_id,
                                    i)
            parts.append({"PartNumber": i, "ETag": part["ETag"]})
            i += 1
            

            while log_file["AdditionalDataPending"]:
                #print(log_file["Marker"])
                log_file = dwl(self.db_identifier, log["LogFileName"], log_file["Marker"])
                log_file_data = log_file["LogFileData"]

                part = self.upload_s3_part(
                                        log_file_data,
                                        id_file_log,
                                        mpu_id,
                                        i)
                parts.append({"PartNumber": i, "ETag": part["ETag"]})
                i += 1
                #print("uploading part: {}".format(i))

            result = self.complete_s3_upload(id_file_log, mpu_id, parts)
            self.logger.info("upload finished {}".format(id_file_log))

     

    ### S3
    def create_s3_mpu(self, file_name):
        return self.s3_client.create_multipart_upload(
                    Bucket=config.aws_bucket_instance,
                    Key=file_name)["UploadId"]


    def upload_s3_part(self, log_file_data, id_file_log, mpu_id, part_id):
        return self.s3_client.upload_part(
                                            Body=log_file_data,
                                            Bucket=config.aws_bucket_instance,
                                            Key=id_file_log,
                                            UploadId=mpu_id,
                                            PartNumber=part_id)


    def complete_s3_upload(self, id_file_log, mpu_id, parts):
        return self.s3_client.complete_multipart_upload(
                                    Bucket=config.aws_bucket_instance,
                                    Key=id_file_log,
                                    UploadId=mpu_id,
                                    MultipartUpload={"Parts": parts})
 
 

def lambda_handler(event, context):
    rds_client = boto3.client("rds",
                            region_name=config.aws_region)
    s3_client = boto3.client("s3",
                            region_name=config.aws_region)
    app = App(rds_client=rds_client, s3_client=s3_client) 


if __name__ == "__main__":
    rds_client = boto3.client("rds",
                            region_name=config.aws_region,
                            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"])
    s3_client = boto3.client("s3",
                            region_name=config.aws_region,
                            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"])
    app = App(rds_client=rds_client, s3_client=s3_client, debug=True) 
