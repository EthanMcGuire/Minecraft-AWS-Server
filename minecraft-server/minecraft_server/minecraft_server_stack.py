from aws_cdk import (
    # Duration,
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_iam as iam,
    aws_ec2 as ec2
)

import aws_cdk as cdk

from constructs import Construct

USER_DATA_FILE = "initialize.sh"

bucket_name = "minecraftserverstack-ccfpminecraftserver329202397-120m63ljzb68g"
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["s3:ListBucket"],
            "Resource": [f"arn:aws:s3:::{bucket_name}"]
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
            "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
        }
    ]
}

myIp = '73.218.214.71/32'

class MinecraftServerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #Server files bucket
        bucket = s3.Bucket(self, "CCFP-minecraft-server-3/29/2023", versioned=True)

        deployment = s3_deployment.BucketDeployment(self, "DeployServer",
            sources=[s3_deployment.Source.asset("./server-files")],
            destination_bucket=bucket)
        
        #Create EC2 policy to access the bucket
        policy_document = iam.PolicyDocument.from_json(bucket_policy)

        new_policy = iam.Policy(self, "CCFP-minecraft-s3-policy",
                    document=policy_document)
        
        #EC2 role which will hold this policy
        ec2Role = iam.Role(self,'CCFP-minecraft-s3-role', assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'))

        ec2Role.attach_inline_policy(new_policy)

        ###Creating the EC2 instance

        #VPC
        defaultVpc = ec2.Vpc.from_lookup(self, 'CCFP-minecraft-VPC', is_default=True)

        #Create the security group
        #A security group acts as a virtual firewall for your instance to control inbound and outbound traffic.
        securityGroup = ec2.SecurityGroup(self,'CCFP-minecraft-sg', vpc=defaultVpc, allow_all_outbound=True, security_group_name='CCFP-minecraft-sg')

        #Allow inbound traffic on specific ports
        securityGroup.add_ingress_rule(ec2.Peer.ipv4(myIp), ec2.Port.tcp(22), description='Allows SSH access for Admin')  #Only allow SSH to myself
        securityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(25565), description='Allows minecraft access')
        securityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.udp(25565), description='Allows minecraft access')

        #User data script
        with open(USER_DATA_FILE, "r") as f:
            user_data_script = f.read()

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(user_data_script)

        # #EC2 instance
        # instance = ec2.Instance(self, 'CCFP-minecraft-ec2-instance', vpc= defaultVpc, role=ec2Role, security_group=securityGroup, instance_name='CCFP-minecraft-ec2-instance',\
        #                         instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MEDIUM), machine_image=ec2.MachineImage.latest_amazon_linux(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),\
        #                         key_name= 'CCFP-minecraft-key', user_data=user_data)

        # #We want the ip address of this new instance so we can ssh into it later
        # output = cdk.CfnOutput(self, 'CCFP-minecraft-output', value=instance.instance_public_ip)