import boto3
import argparse
import json
import sys
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

def delete_resource(session, arn, region):
    try:
        service = arn.split(':')[2]
        resource_type = arn.split(':')[5].split('/')[0] if '/' in arn else ''
        resource_id = arn.split('/')[-1] if '/' in arn else arn.split(':')[-1]

        if service == 'ec2' and resource_type == 'instance':
            ec2_client = session.client('ec2', region_name=region)
            ec2_client.terminate_instances(InstanceIds=[resource_id])
            return f"Terminated EC2 instance: {resource_id}"
        
        elif service == 'rds' and resource_type == 'db':
            rds_client = session.client('rds', region_name=region)
            rds_client.delete_db_instance(DBInstanceIdentifier=resource_id, SkipFinalSnapshot=True)
            return f"Deleted RDS instance: {resource_id}"
        
        elif service == 'sqs':
            sqs_client = session.client('sqs', region_name=region)
            sqs_client.delete_queue(QueueUrl=resource_id)
            return f"Deleted SQS queue: {resource_id}"
        
        elif service == 'secretsmanager':
            secrets_client = session.client('secretsmanager', region_name=region)
            secrets_client.delete_secret(SecretId=resource_id, ForceDeleteWithoutRecovery=True)
            return f"Deleted Secrets Manager secret: {resource_id}"
        
        elif service == 's3':
            s3_client = session.client('s3', region_name=region)
            s3_client.delete_bucket(Bucket=resource_id)
            return f"Deleted S3 bucket: {resource_id}"
        
        else:
            return f"Unsupported resource type for deletion: {service} ({arn})"
    except ClientError as e:
        return f"Error deleting {arn}: {e}"

def main():
    parser = argparse.ArgumentParser(description="AWS Resource Deletion Script")
    parser.add_argument('--profile', required=True, help="AWS profile name")
    parser.add_argument('--region', required=True, help="AWS region")
    parser.add_argument('--json-file', required=True, help="JSON file containing ARNs to delete")
    args = parser.parse_args()

    try:
        with open(args.json_file, 'r') as f:
            arns = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file {args.json_file}: {e}")
        sys.exit(1)

    if not arns:
        print("No ARNs found in the JSON file. Exiting.")
        sys.exit(0)

    print("\nResources to be deleted:")
    print("-----------------------")
    for arn in arns:
        print(arn)
    print("-----------------------")
    confirmation = input("Confirm deletion of these resources? (y/n): ").strip().lower()

    if confirmation != 'y':
        print("Deletion cancelled.")
        sys.exit(0)

    try:
        session = boto3.Session(profile_name=args.profile)
        print(f"\nProcessing deletions for profile {args.profile} in region {args.region}")
        for arn in arns:
            result = delete_resource(session, arn, args.region)
            print(result)
    except ProfileNotFound:
        print(f"Profile {args.profile} not found.")
        sys.exit(1)
    except NoCredentialsError:
        print(f"No credentials found for profile {args.profile}.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during deletion process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()