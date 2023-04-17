import boto3
import json
import os

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    ec2.start_instances(InstanceIds=[os.environ['INSTANCE_ID']])
    return {
        'statusCode': 200,
        'body': json.dumps('Turned server on.')
    }
