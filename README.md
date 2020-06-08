# logstash
Busca logs de auditoria do RDS e salva no S3

## testes

### Requirimentos 
 1. docker
 2. Usuário do aws (não root) com a police 'PowerUserAccess'
### instalação
```
docker pull centos
docker ps
docker exec -it admiring_engelbart /bin/bash
yum update
yum install python3
yum install git
yum install vim
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py
pip3 install boto3
pip3 install pyyaml
pip3 install PyMySQL
adduser gans
su - gans
git clone https://github.com/gans/logstash.git
cd logstash
```
install Terraform https://learn.hashicorp.com/terraform/getting-started/install.html

#### Exporte as variáveis de acesso ao aws:

export AWS_ACCESS_KEY_ID=somevalue

export AWS_SECRET_ACCESS_KEY=somevalue

export AWS_DEFAULT_REGION="us-east-2"

### Inicialize os recursos aws

```
cd logstash/aws_resources
terraform init
terraform plan --out rds-plan
terraform apply "rds-plan"
```

### Inicialize mock de dados:
```
mysql -h [hostrds troque].us-east-2.rds.amazonaws.com -P 3306 -u hotmart -p -e "CREATE DATABASE hotmart"
mysql -h [hostrds troque].us-east-2.rds.amazonaws.com -P 3306 -u hotmart -p -e "USE hotmart; CREATE TABLE IF NOT EXISTS sales (id VARCHAR(23), ts_sale DATETIME, name VARCHAR(23));"
```
Edite os dados em config.yaml e rode o app de mock:
```
python3 mock_mysql.py
```
Com isso será gerado arquivos de logs de 100Kb, dessa forma possibilitando executar testes locais.

### Teste o envio de logs
Edite o arquivo app.py e modifique as variáveis RDS_ID, AWS_REGION, BUCKET_NAME, AWS_ACCESS_ID, AWS_SECRET e rode o script:
```
python3 app.py
```
Se tudo estiver correto o S3 ira conter os logs.


## Produção
Modifique os arquivos aws_lambda/lambda.tf e aws_resources/main.tf com os valores de produção caso necessário. Execute a implantação dos recursos e função lambda:

```
cd logstash/aws_resources
terraform init
terraform plan --out rds-plan
terraform apply "rds-plan"

cd logstash/aws_lambda
terraform init
terraform plan --out rds-plan
terraform apply "rds-plan"
```
