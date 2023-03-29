from aws_cdk import (
    # Duration,
    Stack,
    aws_sqs as sqs,
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_cloudwatch as cw

)
from constructs import Construct

class FinalProjectStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(self, "minecraft-server-files-3/29/2023")

        # The code that defines your stack goes here

        # example resource
        # queue = sqs.Queue(
        #     self, "FinalProjectQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
