# Minecraft-AWS-Server
 Minecraft server hosted through AWS.

 To create AWS resources on a terminal do:
    CDK synth --parameters myIp={insert-admin-ip}
    CDK deploy --parameters myIp={insert-admin-ip}

--profile name might be required after each command

Synth synthesizes the resources
Deploy deploys the resources to AWS

Resources are defined in final_project_stack.py

SOME USEFUL CDK INFORMATION FOR STARTING:
    https://docs.aws.amazon.com/cdk/v2/guide/hello_world.html

SET AWS USER INFORMATION:
    In app.py, change the account you are running on:
        MinecraftServerStack(app, "MinecraftServerStack", env=cdk.Environment(account='352387159701', region='us-east-1'))
        -The account ID and region should be those of your AWS account

    Your command line or visual studio AWS account should also be configured with the proper keys and credentials.

SSH:
    In minecraft_server_stack.py the IP for being able to SSH into the EC2 instance should be changed if you want that access. If you upload the server on your account, this can also
    be changed in the EC2's security group on AWS -> EC2 instances.

INSTALLATION:
    https://docs.npmjs.com/downloading-and-installing-node-js-and-npm

    FIRST:
        Install Node.js
        Then install NPM: npm install -g npm

    NEXT:
        npm install -g npm

    FINALLY:
        #Do this in the project directory
        python -m pip install -r requirements.txt   #This will install the requirements of the CDK project

Once all this is done, you can deploy.

HOW TO RUN:
    On command line:
        CDK ls      #This lists all stacks in your project (Just a test to make sure its working)
        CDK Synth --parameters myIp={insert-admin-ip} #Only needs to be done once (Per directory I think? So might not even need to)
        CDK Deploy --parameters myIp={insert-admin-ip}