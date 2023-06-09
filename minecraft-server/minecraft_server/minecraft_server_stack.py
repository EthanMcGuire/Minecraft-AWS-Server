from aws_cdk import (
    # Duration,
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_sns_subscriptions as subs
)

import aws_cdk as cdk

import os

from constructs import Construct

USER_DATA_FILE = "initialize.sh"
WORLD_NAME = "Cloud Computing Server"

class MinecraftServerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        myIp = cdk.CfnParameter(self, "myIp", type="String",
            description="The IP address of the admin. Used to limit SSH access to the EC2 server.")

        #Server files bucket
        bucket = s3.Bucket(self, "CCFP-minecraft-server-3/29/2023", versioned=True)

        deployment = s3_deployment.BucketDeployment(self, "DeployServer",
            sources=[s3_deployment.Source.asset("./server-files")],
            destination_bucket=bucket)

        #Create the EC2 policy to access the bucket, and update SSM information
        ec2_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["s3:ListBucket"],
                    "Resource": [f"arn:aws:s3:::{bucket.bucket_name}"]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:ListBucket",
                        "s3:GetObject",
                        "s3:GetBucketLocation",
                        "s3:PutObject",
                        "s3:PutObjectAcl",
                        "s3:DeleteObject"
                    ],
                    "Resource": [f"arn:aws:s3:::{bucket.bucket_name}/*"]
                },
                {
                    "Effect": "Allow",
                    "Action": "ssm:UpdateInstanceInformation",
                    "Resource": "*"
                }
            ]
        }

        policy_document = iam.PolicyDocument.from_json(ec2_policy)

        ec2_policy = iam.Policy(self, "CCFP-minecraft-ec2-policy",
                    document=policy_document)

        #EC2 role which will hold this policy
        #Use managed polcies to add SSM policies
        ec2Role = iam.Role(self,'CCFP-minecraft-ec2-role', assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'))

        ec2Role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        ec2Role.attach_inline_policy(ec2_policy)

        #Profile for the EC2 role
        instance_profile = iam.CfnInstanceProfile(self, "CCFP-minecraft-instance-profile", roles=[ec2Role.role_name])

        ###Creating the EC2 instance

        #VPC
        defaultVpc = ec2.Vpc.from_lookup(self, 'CCFP-minecraft-VPC', is_default=True)

        #Create the security group
        #A security group acts as a virtual firewall for your instance to control inbound and outbound traffic.
        securityGroup = ec2.SecurityGroup(self,'CCFP-minecraft-sg', vpc=defaultVpc, allow_all_outbound=True, security_group_name='CCFP-minecraft-sg')

        #Allow inbound traffic on specific ports
        securityGroup.add_ingress_rule(ec2.Peer.ipv4(myIp.value_as_string + '/32'), ec2.Port.tcp(22), description='Allows SSH access for Admin')  #Only allow SSH to myself
        securityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(25565), description='Allows minecraft access')
        securityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.udp(25565), description='Allows minecraft access')

        #User data script
        with open(USER_DATA_FILE, "r") as f:
            user_data_script = f.read()
        user_data_script = user_data_script.replace('${S3_BUCKET_NAME}', bucket.bucket_name)

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(user_data_script)

        #EC2 instance
        instance = ec2.Instance(self, 'CCFP-minecraft-ec2-instance', vpc= defaultVpc, role=ec2Role, security_group=securityGroup, instance_name='CCFP-minecraft-ec2-instance',\
                                instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM), machine_image=ec2.MachineImage.latest_amazon_linux(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),\
                                key_name= 'CCFP-minecraft-key', user_data=user_data)

        #Create an elastic IP address (EIP)
        eIp = ec2.CfnEIP(
            self, "CCFP-minecraft-EIP",
            domain="vpc",
        )

        #Associate the EIP with the server EC2 instance
        eIpAssoc = ec2.CfnEIPAssociation(
            self, "CCFP-minecraft-EIP-Assoc",
            instance_id=instance.instance_id,
            allocation_id=eIp.attr_allocation_id,
        )

        ### Cloudwatch Backups

        # Create the IAM policy and role for the Lambda function

        # Create the lambda policy
        lambda_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:*"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                },
                {
                    "Effect": "Allow",
                    "Action": "s3:PutObject",
                    "Resource": [f"arn:aws:s3:::{bucket.bucket_name}/*"]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:Describe*",
                        "ssm:SendCommand",
                        "ssm:GetCommandInvocation"
                    ],
                    "Resource": "*"
                }
            ]
        }

        policy_document = iam.PolicyDocument.from_json(lambda_policy)

        lambda_policy = iam.Policy(self, "CCFP-minecraft-lambda-policy",
                                document=policy_document)

        # Lambda role
        lambda_role = iam.Role(self,"CCFP-minecraft-LambdaBackupRole", assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'))

        lambda_role.attach_inline_policy(lambda_policy)

        # Allow the Lambda function to put objects into the S3 bucket
        bucket.grant_put(lambda_role)

        # Grant permission to the EC2 instance to write to the S3 bucket
        bucket.grant_write(instance.role)

        # Create the Lambda function
        backup_lambda = _lambda.Function(self, "CCFP-minecraft-LambdaBackup",
                                          runtime=_lambda.Runtime.PYTHON_3_8,
                                          handler="lambda_backup.lambda_handler",
                                          code=_lambda.Code.from_asset('lambda'),
                                          role=lambda_role,
                                          timeout=cdk.Duration.seconds(30),
                                          environment = {
                                            'INSTANCE_ID': instance.instance_id,
                                            'BUCKET_NAME': bucket.bucket_name,
                                            'WORLD_NAME': WORLD_NAME
                                          })

        # Create the CloudWatch rule to trigger the Lambda function every 5 minutes
        backup_rule = events.Rule(self, "CCFP-minecraft-BackupRule",
                                   schedule=events.Schedule.cron(minute="*/5"),
                                   targets=[targets.LambdaFunction(handler=backup_lambda)])

        ### Server On/Off webpage

        # Create Lambda functions to turn the EC2 server on and off
        server_on_lambda = _lambda.Function(
            self, "CCFP-minecraft-LambdaOn",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="server_on.lambda_handler",
            code=_lambda.Code.from_asset('lambda'),
            environment={
                'INSTANCE_ID': instance.instance_id
            }
        )

        server_off_lambda = _lambda.Function(
            self, "CCFP-minecraft-LambdaOff",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="server_off.lambda_handler",
            code=_lambda.Code.from_asset('lambda'),
            environment={
                'INSTANCE_ID': instance.instance_id
            }
        )

        # Create URLs for the on/off Lambda functions
        server_on_fn_url = server_on_lambda.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE
        )
        server_off_fn_url = server_off_lambda.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE
        )

        # Create and assign appropriate policies for the on/off Lambda functions
        ec2_start_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["ec2:Start*"],
            resources=[
                f"arn:aws:ec2:{os.environ['CDK_DEFAULT_REGION']}" \
                f":{os.environ['CDK_DEFAULT_ACCOUNT']}" \
                f":instance/{instance.instance_id}"
            ]
        )

        server_on_lambda.role.add_to_policy(ec2_start_policy_statement)

        ec2_stop_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["ec2:Stop*"],
            resources=[
                f"arn:aws:ec2:{os.environ['CDK_DEFAULT_REGION']}" \
                f":{os.environ['CDK_DEFAULT_ACCOUNT']}" \
                f":instance/{instance.instance_id}"
            ]
        )

        server_off_lambda.role.add_to_policy(ec2_stop_policy_statement)

        # Create a Lambda function which displays a webpage to turn the server on or off
        server_webpage_lambda = _lambda.Function(
            self, "CCFP-minecraft-LambdaWebpage",
            runtime=_lambda.Runtime.NODEJS_14_X,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                'INSTANCE_ID': instance.instance_id,
                'ON_URL': server_on_fn_url.url,
                'OFF_URL': server_off_fn_url.url
            }
        )

        # Create public URL for the status webpage
        webpage_url = server_webpage_lambda.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE
        )

        # Create and assign appropriate policy to the webpage Lambda function
        call_lambda_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "lambda:InvokeFunction"
            ],
            resources=[
                server_on_lambda.function_arn,
                server_off_lambda.function_arn
            ]
        )

        ec2_describe_policy_statement = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceStatus"
            ],
            resources=["*"]
        )

        server_webpage_lambda.role.add_to_policy(call_lambda_policy_statement)
        server_webpage_lambda.role.add_to_policy(ec2_describe_policy_statement)

        # Output the server's IP address the URL of the on/off webpage
        cdk.CfnOutput(self, 'CCFP-minecraft-server-IP', value=instance.instance_public_ip)
        cdk.CfnOutput(self, 'CCFP-minecraft-webpage-URL', value=webpage_url.url)
