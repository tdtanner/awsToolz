#!/bin/bash
snapshots_to_delete=$(aws --profile oldprod ec2 describe-snapshots --owner-ids xxxxxxxxxxx --query 'Snapshots[?StartTime<=`2020-06-27`].SnapshotId' --output json | tr -d '"' | tr ',' '\n' | tr -d '[]' | sed '/^$/d')
# adjust your date range by modifying the string after StartTime
echo "List of snapshots to delete: $snapshots_to_delete"
# delete dem shits dont forget to add the right profile or I will keeeeel you
for snap in $snapshots_to_delete; do
  aws --profile oldprod ec2 delete-snapshot --snapshot-id $snap
done
