# Minecraft-AWS-Server
Minecraft server hosted through AWS. Created by Mason Charette, Raymond Fanini, Ethan McGuire, and Sahil Patel for COMP.4600 - Cloud Computing at UMass Lowell.

## Usage
To run the Cloud Development Kit (CDK) code and deploy the AWS stack for this project, run the following on your terminal.
```
cdk synth --parameters myIp={insert-admin-ip}

cdk deploy --parameters myIp={insert-admin-ip}
```

Synth creates a CloudFormation template for the project, while deploy actually create the resources on AWS.

The provided IP address is used to limit SSH access to the EC2 instance which runs the server. In particular, only devices from that IP are allowed to SSH into the server.

## Relevant Files
Many boilerplate files are created during CDK project initialization. Here is a listing of the files which we've written or placed that are relevant to project.

`minecraft-server/app.py` - Initializes the application and the single stack deployed by our project.
`minecraft-server/minecraft-server/minecraft_server_stack.py` - The majority of the project lives here. Defines all of the resources (EC2, Lambdas, S3, Policies, Roles, etc.) used.
`minecraft-server/lambda/*` - The source code for all of our Lambda functions.
`minecraft-server/server-files/*` - Files initially placed into our S3 Bucket. They are used to initialize the server on the EC2 instance.
`minecraft-server/initialize.sh` - The user-data script for our EC2 instance. Installs the necessary software and downloads relevant files from the S3 Bucket.

## Information for First Time Users
If you've never used the CDK before, check out this link.
https://docs.aws.amazon.com/cdk/v2/guide/hello_world.html

Your command line or Visual Studio AWS account should also be configured with the proper keys and credentials.

Here are some prerequisites to the CDK and our project.
```
INSTALLATION:
    https://docs.npmjs.com/downloading-and-installing-node-js-and-npm

FIRST:
    Install Node.js
    Then install NPM: npm install -g npm

NEXT:
    npm install -g npm

FINALLY:
    #Do this in the project directory
    #This will install the requirements of the CDK project
    python -m pip install -r requirements.txt
```

Once all this is done, you can deploy our CDK code.
```
cdk ls #This lists all stacks in your project (Just a test to make sure its working)

cdk Synth --parameters myIp={insert-admin-ip} #Generates a CloudFormation template

cdk Deploy --parameters myIp={insert-admin-ip}
```
