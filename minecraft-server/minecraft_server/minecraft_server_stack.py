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

from constructs import Construct

USER_DATA_FILE = "initialize.sh"

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

        #Create the EC2 policy to access the bucket
        bucket_policy = {
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
                }
            ]
        }

        policy_document = iam.PolicyDocument.from_json(bucket_policy)

        new_policy = iam.Policy(self, "CCFP-minecraft-s3-policy",
                    document=policy_document)

        #EC2 role which will hold this policy
        ec2Role = iam.Role(self,'CCFP-minecraft-s3-role', assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'))

        ec2Role.attach_inline_policy(new_policy)

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

        #We want the ip address of this instance
        output = cdk.CfnOutput(self, 'CCFP-minecraft-output', value=instance.instance_public_ip)

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
                                          handler="lambda_function.lambda_handler",
                                          code=_lambda.Code.from_asset('lambda'),
                                          role=lambda_role,
                                          environment = {
                                            'INSTANCE_ID': instance.instance_id,
                                            'BUCKET_NAME': bucket.bucket_name
                                          })

        # Create the CloudWatch rule to trigger the Lambda function every 5 minutes
        backup_rule = events.Rule(self, "CCFP-minecraft-BackupRule",
                                   schedule=events.Schedule.cron(minute="*/5"),
                                   targets=[targets.LambdaFunction(handler=backup_lambda)])

        #Do this later

        # # Create the CloudWatch alarm to monitor the S3 bucket for failures
        # backup_alarm = cloudwatch.Alarm(self, "CCFP-minecraft-BackupAlarm",
        #                                 metric=bucket.metric_all_objects(),
        #                                 evaluation_periods=1,
        #                                 threshold=0,
        #                                 alarm_description="No objects have been added to the backup bucket in the last 5 minutes.",
        #                                 alarm_name="CCFP-minecraft-BackupAlarm")

        # # Add the alarm action to the CloudWatch rule
        # backup_alarm.add_alarm_action(subs.SnsAction(backup_notification_topic)