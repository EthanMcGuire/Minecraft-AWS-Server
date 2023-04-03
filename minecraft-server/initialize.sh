#!/usr/bin/env/ bash
sudo yum -y install java-1.8.0
sudo mkdir /minecraft
sudo chown -R ec2-user:ec2-user /minecraft
cd /minecraft
aws s3 cp s3://minecraftserverstack-ccfpminecraftserver329202397-120m63ljzb68g/forge-1.19.3-44.1.0-installer.jar .
java -jar forge-1.19.3-44.1.0-installer.jar --installServer
echo '#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://account.mojang.com/documents/minecraft_eula).
#Sun Apr 02 15:11:12 EDT 2023
eula=true
' > eula.txt
sudo aws s3 cp s3://minecraftserverstack-ccfpminecraftserver329202397-120m63ljzb68g/server.properties .
sudo aws s3 cp s3://minecraftserverstack-ccfpminecraftserver329202397-120m63ljzb68g/minecraft.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl start minecraft