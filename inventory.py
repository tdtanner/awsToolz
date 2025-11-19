import boto3
import pandas as pd
import argparse
import json
from datetime import datetime
import sys
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

def get_all_resources(session, region):
    try:
        resourcegroupstaggingapi_client = session.client('resourcegroupstaggingapi', region_name=region)
        paginator = resourcegroupstaggingapi_client.get_paginator('get_resources')
        resources = []
        for page in paginator.paginate():
            for resource in page['ResourceTagMappingList']:
                arn = resource.get('ResourceARN', 'N/A')
                resource_type = arn.split(':')[2] if ':' in arn else 'Unknown'
                resources.append({
                    'ResourceARN': arn,
                    'ResourceType': resource_type,
                    'Region': region,
                    'Tags': '; '.join([f"{tag['Key']}={tag['Value']}" for tag in resource.get('Tags', [])]) or 'N/A'
                })
        return resources
    except ClientError as e:
        print(f"Error retrieving resources in {region}: {e}")
        return []

def organize_resources_by_type(resources):
    organized_data = {}
    for resource in resources:
        resource_type = resource['ResourceType']
        if resource_type not in organized_data:
            organized_data[resource_type] = []
        organized_data[resource_type].append(resource)
    return organized_data

def save_arns_to_json(data, output_dir):
    try:
        for resource_type, records in data.items():
            if records:
                arns = [record['ResourceARN'] for record in records]
                json_filename = f"{output_dir}/{resource_type}.json"
                with open(json_filename, 'w') as f:
                    json.dump(arns, f, indent=2)
                print(f"Saved ARNs to {json_filename}")
    except Exception as e:
        print(f"Error writing JSON files: {e}")

def create_excel_output(data, output_file):
    try:
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            for resource_type, records in data.items():
                if records:
                    sheet_name = resource_type.replace(':', '_').replace('/', '_')[:31]
                    df = pd.DataFrame(records)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    worksheet = writer.sheets[sheet_name]
                    for idx, col in enumerate(df.columns):
                        max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(idx, idx, max_len)
        print(f"Inventory written to {output_file}")
    except Exception as e:
        print(f"Error writing to Excel file: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AWS Resource Inventory Script")
    parser.add_argument('--profiles', nargs='+', required=True, help="AWS profile names")
    parser.add_argument('--regions', nargs='+', required=True, help="AWS regions to scan")
    parser.add_argument('--output-dir', default='.', help="Directory to save JSON files")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{args.output_dir}/aws_inventory_{timestamp}.xlsx"
    all_resources = []

    for profile in args.profiles:
        try:
            session = boto3.Session(profile_name=profile)
            print(f"Processing profile: {profile}")
            for region in args.regions:
                print(f"Scanning region: {region}")
                all_resources.extend(get_all_resources(session, region))
        except ProfileNotFound:
            print(f"Profile {profile} not found. Skipping.")
        except NoCredentialsError:
            print(f"No credentials found for profile {profile}. Skipping.")
        except Exception as e:
            print(f"Error processing profile {profile}: {e}")

    organized_data = organize_resources_by_type(all_resources)
    create_excel_output(organized_data, output_file)
    save_arns_to_json(organized_data, args.output_dir)

if __name__ == "__main__":
    main()