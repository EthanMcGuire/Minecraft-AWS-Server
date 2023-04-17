import boto3
import os
import time

def lambda_handler(event, context):
    # Get instance id and bucket name
    instance_id = os.environ['INSTANCE_ID']
    bucket_name = os.environ['BUCKET_NAME']
    world_name = os.environ['WORLD_NAME']

    # Use the EC2 SSM to run a command to zip the minecraft/world directory
    ssm_client = boto3.client('ssm')
    ssm_command = f"cd /minecraft && zip -r saves.zip '{world_name}'"

    # Send the command
    ssm_response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': [ssm_command]}
    )

    ssm_command_id = ssm_response['Command']['CommandId']

    # Wait for the command to finish
    tries = 0
    output = 'False'
    while tries < 10:
        tries = tries + 1
        try:
            time.sleep(0.5)  # some delay always required...
            result = ssm_client.get_command_invocation(
                CommandId=ssm_command_id,
                InstanceId=instance_id,
            )

            if result['Status'] == 'InProgress':
                continue

            output = result['StandardOutputContent']
            
            break
        except ssm_client.exceptions.InvocationDoesNotExist:
            continue

    # Use the EC2 SSM to run a command to upload the world.zip file to S3
    ssm_command = f"aws s3 cp /minecraft/saves.zip s3://{bucket_name}/saves.zip"

    # Send the command
    ssm_response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': [ssm_command]}
    )

    ssm_command_id = ssm_response['Command']['CommandId']

    # Wait for the command to finish
    tries = 0
    output = 'False'
    while tries < 10:
        tries = tries + 1
        try:
            time.sleep(0.5)  # some delay always required...
            result = ssm_client.get_command_invocation(
                CommandId=ssm_command_id,
                InstanceId=instance_id,
            )

            if result['Status'] == 'InProgress':
                continue

            output = result['StandardOutputContent']

            break
        except ssm_client.exceptions.InvocationDoesNotExist:
            continue
    
    return {
        'statusCode': 200,
        'body': 'Backup successful!'
    }
