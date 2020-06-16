# logstash
Retrieve audit logs from RDS and put in S3

## Development
In development phase is used a centos docker image to run boto3 commands, a RDS MySQL database and a S3 instance.

### Requirements 
 1. docker
 2. aws user (not root) com a police 'PowerUserAccess'
### Install
```
docker pull centos
docker run --name centos-challenge -i -t centos
yum update
yum -y install python3 git vim unzip mysql.x86_64
cd /tmp
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
pip3 install boto3 PyMySQL
curl https://releases.hashicorp.com/terraform/0.12.26/terraform_0.12.26_linux_amd64.zip -o terraform.zip
unzip terraform.zip
mv terraform /usr/local/bin/
adduser gans
su - gans
git clone https://github.com/gans/logstash.git
cd logstash
```

#### Export the aws keys:

export AWS_ACCESS_KEY_ID=somevalue

export AWS_SECRET_ACCESS_KEY=somevalue

export AWS_DEFAULT_REGION="us-east-2"

### Init the RDS and S3 resources

```
cd logstash/aws_resources
terraform init
terraform plan --out rds-s3-plan
terraform apply "rds-plan"
```

Terraform output will show the rds end point: keep that

### Init date mock:

Edit config.py and change the MySQL host with rds endpoint.

Init the database structure (change the host to rds endpoint). Password is int config.py
```
mysql -h [host] -P 3306 -u hotmart -p -e "CREATE DATABASE logstash"
mysql -h [host] -P 3306 -u hotmart -p -e "USE logstash; CREATE TABLE IF NOT EXISTS sales (id VARCHAR(23), ts_sale DATETIME, name VARCHAR(23));"
```
 Then init the mock:
```
python3 mock_mysql.py
```
This will create logs with 100Kb and tests can be made.

### Sending the logs files to S3

run the bellow command:

```
python3 app.py
```
If no errors can be found the logs files will be in S3.


## Production

```
cd logstash/aws_resources
terraform init
terraform plan --out rds-plan
terraform apply "rds-plan"

cd logstash/aws_lambda
terraform init
terraform plan --out lambda-plan
terraform apply "lambda-plan"
```
