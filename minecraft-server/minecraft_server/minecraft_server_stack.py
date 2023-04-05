from aws_cdk import (
    # Duration,
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_iam as iam,
    aws_ec2 as ec2
)

import aws_cdk as cdk
import boto3
import os

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

myIp = '73.47.135.217/32'

class MinecraftServerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #Server files bucket
        bucket = s3.Bucket(self, "CCFP-minecraft-server-3/29/2023", versioned=True)

        deployment = s3_deployment.BucketDeployment(self, "DeployServer",
            sources=[s3_deployment.Source.asset("./server-files")],
            destination_bucket=bucket)
        
        #Create the EC2 policy to access the bucket
        policy_document = iam.PolicyDocument.from_json(bucket_policy)

        new_policy = iam.Policy(self, "CCFP-minecraft-s3-policy",
                    document=policy_document)
        
        #EC2 role which will hold this policy
        ec2Role = iam.Role(self,'CCFP-minecraft-s3-role', assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'))

        ec2Role.attach_inline_policy(new_policy)

        #Profile for the EC2 role
        instance_profile = iam.CfnInstanceProfile(self, "CCFP-minecraft-instance-profile", roles=[ec2Role.role_name])

        #Create the spot pricing role for the EC2 instance
        spot_fleet_role = iam.Role(
            self, "CCFP-minecraft-SpotFleetRole",
            assumed_by=iam.ServicePrincipal('spotfleet.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonEC2SpotFleetTaggingRole'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore')
            ]
        )

        #Grant additional permissions as needed
        spot_fleet_role.add_to_policy(iam.PolicyStatement(
            actions=["ec2:*"],
            resources=["*"]
        ))

        ###Creating the EC2 instance

        # #VPC
        # defaultVpc = ec2.Vpc.from_lookup(self, 'CCFP-minecraft-VPC', is_default=True)

        # #Create the security group
        # #A security group acts as a virtual firewall for your instance to control inbound and outbound traffic.
        # securityGroup = ec2.SecurityGroup(self,'CCFP-minecraft-sg', vpc=defaultVpc, allow_all_outbound=True, security_group_name='CCFP-minecraft-sg')

        # #Allow inbound traffic on specific ports
        # securityGroup.add_ingress_rule(ec2.Peer.ipv4(myIp), ec2.Port.tcp(22), description='Allows SSH access for Admin')  #Only allow SSH to myself
        # securityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(25565), description='Allows minecraft access')
        # securityGroup.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.udp(25565), description='Allows minecraft access')

        # #User data script
        # with open(USER_DATA_FILE, "r") as f:
        #     user_data_script = f.read()

        # user_data = ec2.UserData.for_linux()
        # user_data.add_commands(user_data_script)

        # #OG EC2
        # #EC2 instance
        # instance = ec2.Instance(self, 'CCFP-minecraft-ec2-instance', vpc= defaultVpc, role=ec2Role, security_group=securityGroup, instance_name='CCFP-minecraft-ec2-instance',\
        #                         instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM), machine_image=ec2.MachineImage.latest_amazon_linux(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),\
        #                         key_name= 'CCFP-minecraft-key', user_data=user_data)

        # #We want the ip address of this instance
        # output = cdk.CfnOutput(self, 'CCFP-minecraft-output', value=instance.instance_public_ip)

        # #EC2 spot fleet instance
        # spot_price = "0.04"

        # instance = ec2.CfnSpotFleet(
        #     self, "CCFP-minecraft-SpotFleet",
        #     spot_fleet_request_config_data={
        #         "iamFleetRole": spot_fleet_role.role_arn,
        #         "targetCapacity": 1,
        #         "launchSpecifications": [
        #             {
        #                 "iamInstanceProfile": {"arn": instance_profile.attr_arn},
        #                 "instanceType": "t3.medium",
        #                 "imageId": ec2.MachineImage.latest_amazon_linux(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2).get_image(self).image_id,
        #                 "keyName": "CCFP-minecraft-key",
        #                 "spotPrice": spot_price,
        #                 "UserData": user_data,
        #                 "networkInterfaces": 
        #                 [
        #                     {
        #                         "associatePublicIpAddress": True,
        #                         "deviceIndex": 0,
        #                         "subnetId": defaultVpc.public_subnets[0].subnet_id,
        #                         "groups": [securityGroup.security_group_id],
        #                     },
        #                 ],
        #                 "TagSpecifications": 
        #                 [
        #                     {
        #                         "ResourceType": "instance",
        #                         "Tags": [
        #                         {
        #                             "Key": "CCFP-minecraft-ec2-tag",
        #                             "Value": "CCFP-minecraft-ec2-instance"
        #                         }
        #                         ]
        #                     }
        #                 ],
        #             },
        #         ],
        #     },
        # )

        # client = boto3.client('ec2')

        # response = client.describe_instances(Filters=[  {    'Name': 'tag:CCFP-minecraft-ec2-tag',    'Values': ['CCFP-minecraft-ec2-instance']}])

        # ip_address = response['Reservations'][0]['Instances'][0]['PublicIpAddress']

        # print(ip_address)