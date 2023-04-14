import boto3
import os

def lambda_handler(event, context):
    # Get instance id and bucket name
    instance_id = os.environ['INSTANCE_ID']
    bucket_name = os.environ['BUCKET_NAME']

    # Use the EC2 SSM to run a command to zip the minecraft/saves directory
    ssm_client = boto3.client('ssm')
    ssm_command = f"cd /minecraft && zip -r saves.zip saves"

    # Send the command
    ssm_response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': [ssm_command]}
    )

    ssm_command_id = ssm_response['Command']['CommandId']

    # Wait for the command to finish
    ssm_waiter = ssm_client.get_waiter('command_executed')

    ssm_waiter.wait(
        InstanceIds=[instance_id],
        CommandId=ssm_command_id
    )

    # Use the EC2 SSM to run a command to upload the saves.zip file to S3
    ssm_command = f"aws s3 cp saves.zip s3://{bucket_name}/saves.zip"

    # Send the command
    ssm_response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': [ssm_command]}
    )

    ssm_command_id = ssm_response['Command']['CommandId']

    # Wait for the command to finish
    ssm_waiter = ssm_client.get_waiter('command_executed')
    ssm_waiter.wait(
        InstanceIds=[instance_id],
        CommandId=ssm_command_id
    )
    
    return {
        'statusCode': 200,
        'body': 'Backup successful!'
    }