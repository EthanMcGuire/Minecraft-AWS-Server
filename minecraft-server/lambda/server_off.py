import boto3
import json
import os

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    ec2.stop_instances(InstanceIds=[os.environ['INSTANCE_ID']])
    return {
        'statusCode': 200,
        'body': json.dumps('Turned server off.')
    }
