"""
AWS Resource Deletion Module
Handles deletion of AWS resources with dependency management
"""
import boto3
from typing import List, Dict
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AWSDestroyer:
    """Handles AWS resource deletion with dependency awareness"""

    def __init__(self, profile_name: str, region: str):
        self.profile_name = profile_name
        self.region = region
        self.session = boto3.Session(profile_name=profile_name, region_name=region)
        self.deletion_results = []

    def delete_resources(self, resource_type: str, resource_ids: List[str]) -> List[Dict]:
        """Delete resources based on type"""
        results = []

        deletion_methods = {
            'lambda': self.delete_lambda,
            'api_gateway': self.delete_api_gateway,
            'sqs': self.delete_sqs,
            'ec2': self.delete_ec2,
            'cloudwatch_logs': self.delete_cloudwatch_logs,
            'ebs': self.delete_ebs,
            's3': self.delete_s3
        }

        if resource_type in deletion_methods:
            for resource_id in resource_ids:
                result = deletion_methods[resource_type](resource_id)
                results.append(result)

        return results

    def delete_lambda(self, function_name: str) -> Dict:
        """Delete Lambda function"""
        try:
            client = self.session.client('lambda')
            client.delete_function(FunctionName=function_name)
            logger.info(f"Deleted Lambda function: {function_name}")
            return {'resource': function_name, 'status': 'deleted', 'type': 'lambda'}
        except Exception as e:
            logger.error(f"Error deleting Lambda {function_name}: {e}")
            return {'resource': function_name, 'status': 'failed', 'error': str(e), 'type': 'lambda'}

    def delete_api_gateway(self, api_id: str) -> Dict:
        """Delete API Gateway REST API"""
        try:
            client = self.session.client('apigateway')
            client.delete_rest_api(restApiId=api_id)
            logger.info(f"Deleted API Gateway: {api_id}")
            return {'resource': api_id, 'status': 'deleted', 'type': 'api_gateway'}
        except Exception as e:
            logger.error(f"Error deleting API Gateway {api_id}: {e}")
            return {'resource': api_id, 'status': 'failed', 'error': str(e), 'type': 'api_gateway'}

    def delete_sqs(self, queue_url: str) -> Dict:
        """Delete SQS queue"""
        try:
            client = self.session.client('sqs')
            client.delete_queue(QueueUrl=queue_url)
            logger.info(f"Deleted SQS queue: {queue_url}")
            return {'resource': queue_url, 'status': 'deleted', 'type': 'sqs'}
        except Exception as e:
            logger.error(f"Error deleting SQS queue {queue_url}: {e}")
            return {'resource': queue_url, 'status': 'failed', 'error': str(e), 'type': 'sqs'}

    def delete_ec2(self, instance_id: str) -> Dict:
        """Delete EC2 instance"""
        try:
            client = self.session.client('ec2')

            # Disable termination protection if enabled
            try:
                client.modify_instance_attribute(
                    InstanceId=instance_id,
                    DisableApiTermination={'Value': False}
                )
            except Exception as e:
                logger.warning(f"Could not disable termination protection for {instance_id}: {e}")

            # Terminate instance
            client.terminate_instances(InstanceIds=[instance_id])
            logger.info(f"Terminated EC2 instance: {instance_id}")
            return {'resource': instance_id, 'status': 'deleted', 'type': 'ec2'}
        except Exception as e:
            logger.error(f"Error deleting EC2 instance {instance_id}: {e}")
            return {'resource': instance_id, 'status': 'failed', 'error': str(e), 'type': 'ec2'}

    def delete_cloudwatch_logs(self, log_group_name: str) -> Dict:
        """Delete CloudWatch Log Group"""
        try:
            client = self.session.client('logs')
            client.delete_log_group(logGroupName=log_group_name)
            logger.info(f"Deleted CloudWatch Log Group: {log_group_name}")
            return {'resource': log_group_name, 'status': 'deleted', 'type': 'cloudwatch_logs'}
        except Exception as e:
            logger.error(f"Error deleting CloudWatch Log Group {log_group_name}: {e}")
            return {'resource': log_group_name, 'status': 'failed', 'error': str(e), 'type': 'cloudwatch_logs'}

    def delete_ebs(self, volume_id: str) -> Dict:
        """Delete EBS volume"""
        try:
            client = self.session.client('ec2')

            # Check if volume is attached
            volume = client.describe_volumes(VolumeIds=[volume_id])['Volumes'][0]

            if volume['Attachments']:
                # Detach volume first
                attachment = volume['Attachments'][0]
                client.detach_volume(VolumeId=volume_id)
                logger.info(f"Detached volume {volume_id} from {attachment['InstanceId']}")

                # Wait for detachment
                waiter = client.get_waiter('volume_available')
                waiter.wait(VolumeIds=[volume_id])

            # Delete volume
            client.delete_volume(VolumeId=volume_id)
            logger.info(f"Deleted EBS volume: {volume_id}")
            return {'resource': volume_id, 'status': 'deleted', 'type': 'ebs'}
        except Exception as e:
            logger.error(f"Error deleting EBS volume {volume_id}: {e}")
            return {'resource': volume_id, 'status': 'failed', 'error': str(e), 'type': 'ebs'}

    def delete_s3(self, bucket_name: str) -> Dict:
        """Delete S3 bucket (empties bucket first)"""
        try:
            client = self.session.client('s3')

            # Empty bucket first
            logger.info(f"Emptying S3 bucket: {bucket_name}")

            # Delete all objects
            paginator = client.get_paginator('list_object_versions')
            for page in paginator.paginate(Bucket=bucket_name):
                # Delete object versions
                versions = page.get('Versions', [])
                if versions:
                    objects = [{'Key': v['Key'], 'VersionId': v['VersionId']} for v in versions]
                    client.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})

                # Delete delete markers
                delete_markers = page.get('DeleteMarkers', [])
                if delete_markers:
                    objects = [{'Key': d['Key'], 'VersionId': d['VersionId']} for d in delete_markers]
                    client.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})

            # Delete bucket
            client.delete_bucket(Bucket=bucket_name)
            logger.info(f"Deleted S3 bucket: {bucket_name}")
            return {'resource': bucket_name, 'status': 'deleted', 'type': 's3'}
        except Exception as e:
            logger.error(f"Error deleting S3 bucket {bucket_name}: {e}")
            return {'resource': bucket_name, 'status': 'failed', 'error': str(e), 'type': 's3'}
