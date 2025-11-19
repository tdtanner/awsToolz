"""
AWS Resource Inventory Module
Discovers resources across various AWS services
"""
import boto3
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AWSInventory:
    """Handles AWS resource discovery across multiple services"""

    def __init__(self, profile_name: str, region: str):
        self.profile_name = profile_name
        self.region = region
        self.session = boto3.Session(profile_name=profile_name, region_name=region)

    def discover_all(self) -> Dict[str, List[Dict]]:
        """Discover all supported AWS resources"""
        inventory = {
            'lambda': self.discover_lambda(),
            'api_gateway': self.discover_api_gateway(),
            'sqs': self.discover_sqs(),
            'ec2': self.discover_ec2(),
            'cloudwatch_logs': self.discover_cloudwatch_logs(),
            'ebs': self.discover_ebs(),
            's3': self.discover_s3()
        }
        return inventory

    def discover_lambda(self) -> List[Dict]:
        """Discover Lambda functions"""
        try:
            client = self.session.client('lambda')
            functions = []
            paginator = client.get_paginator('list_functions')

            for page in paginator.paginate():
                for func in page['Functions']:
                    functions.append({
                        'name': func['FunctionName'],
                        'arn': func['FunctionArn'],
                        'runtime': func.get('Runtime', 'N/A'),
                        'id': func['FunctionName']
                    })

            logger.info(f"Found {len(functions)} Lambda functions")
            return functions
        except Exception as e:
            logger.error(f"Error discovering Lambda functions: {e}")
            return []

    def discover_api_gateway(self) -> List[Dict]:
        """Discover API Gateway REST APIs"""
        try:
            client = self.session.client('apigateway')
            apis = []
            paginator = client.get_paginator('get_rest_apis')

            for page in paginator.paginate():
                for api in page['items']:
                    apis.append({
                        'name': api['name'],
                        'id': api['id'],
                        'created': api.get('createdDate', 'N/A')
                    })

            logger.info(f"Found {len(apis)} API Gateway REST APIs")
            return apis
        except Exception as e:
            logger.error(f"Error discovering API Gateway: {e}")
            return []

    def discover_sqs(self) -> List[Dict]:
        """Discover SQS queues"""
        try:
            client = self.session.client('sqs')
            queues = []

            response = client.list_queues()
            queue_urls = response.get('QueueUrls', [])

            for url in queue_urls:
                queue_name = url.split('/')[-1]
                queues.append({
                    'name': queue_name,
                    'url': url,
                    'id': url
                })

            logger.info(f"Found {len(queues)} SQS queues")
            return queues
        except Exception as e:
            logger.error(f"Error discovering SQS queues: {e}")
            return []

    def discover_ec2(self) -> List[Dict]:
        """Discover EC2 instances"""
        try:
            client = self.session.client('ec2')
            instances = []
            paginator = client.get_paginator('describe_instances')

            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        # Skip terminated instances
                        if instance['State']['Name'] == 'terminated':
                            continue

                        name = 'N/A'
                        if 'Tags' in instance:
                            for tag in instance['Tags']:
                                if tag['Key'] == 'Name':
                                    name = tag['Value']
                                    break

                        instances.append({
                            'name': f"{name} ({instance['InstanceId']})",
                            'id': instance['InstanceId'],
                            'state': instance['State']['Name'],
                            'type': instance['InstanceType']
                        })

            logger.info(f"Found {len(instances)} EC2 instances")
            return instances
        except Exception as e:
            logger.error(f"Error discovering EC2 instances: {e}")
            return []

    def discover_cloudwatch_logs(self) -> List[Dict]:
        """Discover CloudWatch Log Groups"""
        try:
            client = self.session.client('logs')
            log_groups = []
            paginator = client.get_paginator('describe_log_groups')

            for page in paginator.paginate():
                for log_group in page['logGroups']:
                    log_groups.append({
                        'name': log_group['logGroupName'],
                        'id': log_group['logGroupName'],
                        'arn': log_group['arn']
                    })

            logger.info(f"Found {len(log_groups)} CloudWatch Log Groups")
            return log_groups
        except Exception as e:
            logger.error(f"Error discovering CloudWatch Log Groups: {e}")
            return []

    def discover_ebs(self) -> List[Dict]:
        """Discover EBS volumes"""
        try:
            client = self.session.client('ec2')
            volumes = []
            paginator = client.get_paginator('describe_volumes')

            for page in paginator.paginate():
                for volume in page['Volumes']:
                    name = 'N/A'
                    if 'Tags' in volume:
                        for tag in volume['Tags']:
                            if tag['Key'] == 'Name':
                                name = tag['Value']
                                break

                    attached_to = 'Unattached'
                    if volume['Attachments']:
                        attached_to = volume['Attachments'][0]['InstanceId']

                    volumes.append({
                        'name': f"{name} ({volume['VolumeId']})",
                        'id': volume['VolumeId'],
                        'size': f"{volume['Size']} GB",
                        'state': volume['State'],
                        'attached_to': attached_to
                    })

            logger.info(f"Found {len(volumes)} EBS volumes")
            return volumes
        except Exception as e:
            logger.error(f"Error discovering EBS volumes: {e}")
            return []

    def discover_s3(self) -> List[Dict]:
        """Discover S3 buckets in the current region"""
        try:
            client = self.session.client('s3')
            buckets = []

            response = client.list_buckets()

            for bucket in response['Buckets']:
                # Check bucket region
                try:
                    location = client.get_bucket_location(Bucket=bucket['Name'])
                    bucket_region = location['LocationConstraint']
                    # us-east-1 returns None for LocationConstraint
                    if bucket_region is None:
                        bucket_region = 'us-east-1'

                    # Only include buckets in the specified region
                    if bucket_region == self.region:
                        buckets.append({
                            'name': bucket['Name'],
                            'id': bucket['Name'],
                            'created': bucket['CreationDate'].isoformat()
                        })
                except Exception as e:
                    logger.warning(f"Could not determine region for bucket {bucket['Name']}: {e}")

            logger.info(f"Found {len(buckets)} S3 buckets in {self.region}")
            return buckets
        except Exception as e:
            logger.error(f"Error discovering S3 buckets: {e}")
            return []
