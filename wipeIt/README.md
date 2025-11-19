# 🔥 Burn It All Down

AWS Resource Cleanup Tool - A web-based application for discovering and deleting AWS resources across your account.

## Features

- **Resource Discovery**: Automatically inventories AWS resources in a specified profile and region
- **Supported Services**:
  - Lambda Functions
  - API Gateway REST APIs
  - SQS Queues
  - EC2 Instances
  - CloudWatch Log Groups
  - EBS Volumes
  - S3 Buckets
- **Selective Deletion**: Choose specific resources or select all
- **Tab-based Interface**: Organized view by resource type
- **Dependency Handling**: Automatically handles resource dependencies (e.g., detaching EBS volumes, emptying S3 buckets)
- **Post-deletion Refresh**: Automatically re-runs inventory to catch any missed resources

## Prerequisites

- Python 3.8+
- AWS CLI configured with named profiles
- Appropriate AWS IAM permissions for resource discovery and deletion

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure AWS Credentials are Configured**:
   ```bash
   aws configure --profile <your-profile-name>
   ```

## Usage

1. **Start the Application**:
   ```bash
   python app.py
   ```

2. **Open Your Browser**:
   Navigate to `http://127.0.0.1:8080`

3. **Run Inventory**:
   - Enter your AWS profile name (defaults to "default")
   - Enter your AWS region (e.g., "us-east-1")
   - Click "Start Inventory"

4. **Select Resources**:
   - Browse tabs for different resource types
   - Use checkboxes to select resources to delete
   - Use "Select All" / "Deselect All" for bulk operations

5. **Delete Resources**:
   - Click the "🔥 Burn It All Down..." button
   - Confirm the destructive action
   - Watch the deletion progress

6. **Review Results**:
   - Check the results panel for successful/failed deletions
   - Inventory automatically refreshes to show remaining resources

## Safety Considerations

⚠️ **WARNING**: This tool is designed for **destructive operations**. Use with extreme caution!

### Recommended Safety Practices:

1. **Test in Non-Production**: Always test in development/sandbox accounts first
2. **Review Selections Carefully**: Double-check what you're about to delete
3. **Use Specific Profiles**: Use dedicated AWS profiles for cleanup operations
4. **Backup Important Data**: Ensure critical data is backed up
5. **Understand Dependencies**: Some resources may have dependencies not fully handled

### Known Limitations:

- **RDS Deletion Protection**: Must be manually disabled before deletion
- **S3 Versioning**: Large versioned buckets may take time to empty
- **EC2 Termination Protection**: Automatically disabled, but may fail in some cases
- **Rate Limits**: AWS API throttling may occur with large resource counts
- **Cross-region Resources**: Only operates on the specified region (except S3 bucket listing)

## Project Structure

```
wipeIt/
├── app.py                  # Flask application
├── aws_inventory.py        # Resource discovery logic
├── aws_destroyer.py        # Resource deletion logic
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html         # Web interface template
└── static/
    ├── style.css          # Styling
    └── app.js             # Frontend JavaScript
```

## How It Works

### Inventory Phase:
1. Uses boto3 to connect to AWS using specified profile/region
2. Queries each supported service for resources
3. Returns structured data with resource names, IDs, and metadata

### Deletion Phase:
1. Receives selected resource IDs from frontend
2. Handles dependencies (e.g., detaching volumes, emptying buckets)
3. Deletes resources and reports success/failure
4. Automatically refreshes inventory

## Extending the Tool

To add support for additional AWS services:

1. **Add Discovery Method** in `aws_inventory.py`:
   ```python
   def discover_new_service(self) -> List[Dict]:
       # Implementation
       pass
   ```

2. **Add Deletion Method** in `aws_destroyer.py`:
   ```python
   def delete_new_service(self, resource_id: str) -> Dict:
       # Implementation
       pass
   ```

3. **Update Resource Type Names** in `static/app.js`:
   ```javascript
   const resourceTypeNames = {
       'new_service': 'New Service Display Name'
   };
   ```

## Troubleshooting

### "Session expired" Error
Re-run the inventory to refresh your session.

### Resources Not Deleting
- Check IAM permissions
- Review CloudWatch logs for specific errors
- Some resources may have deletion protection enabled

### Slow Performance
- Large numbers of resources may take time
- AWS API rate limits may slow operations
- Consider running in smaller batches

## License

Use at your own risk. This tool performs destructive operations on your AWS infrastructure.

## Contributing

This is a utility tool. Extend and modify as needed for your use case.
