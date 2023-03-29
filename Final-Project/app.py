#!/usr/bin/env python3
import os

import aws_cdk as cdk
# import aws_cdk.aws_ec2 as ec2
# import aws_cdk.aws_s3 as s3
# import aws_cdk.aws_cloudwatch as cw
# import aws_cdk.aws_lambda as lambda_

from final_project.final_project_stack import FinalProjectStack


app = cdk.App()

FinalProjectStack(app, "FinalProjectStack", env=cdk.Environment(account='emcguire', region='us-east-1'))

app.synth()

#https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_roles.html