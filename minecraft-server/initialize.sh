#!/usr/bin/env/ bash
sudo yum install mysql -y
sudo yum update
sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
sudo mkdir /minecraft
sudo chown -R ec2-user:ec2-user /minecraft
sudo yum -y install java
cd /minecraft
aws s3 cp s3://${S3_BUCKET_NAME}/server.jar .
sudo java -jar server.jar --nogui
echo '#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).
#Sun Apr 16 11:02:06 EDT 2023
eula=true
' > eula.txt
sudo aws s3 cp s3://${S3_BUCKET_NAME}/server.properties .
sudo aws s3 cp s3://${S3_BUCKET_NAME}/minecraft.service /etc/systemd/system
sudo chown -R ec2-user:ec2-user /minecraft
sudo systemctl daemon-reload
sudo chmod 644 /etc/systemd/system/minecraft.service
sudo systemctl enable minecraft
sudo systemctl start minecraft
