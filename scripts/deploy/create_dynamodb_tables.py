#!/usr/bin/env python
"""Create DynamoDB tables for churn prediction system."""

import sys
import boto3
from botocore.exceptions import ClientError


def create_churn_scores_table(dynamodb, table_name: str = "churn-scores"):
    """Create churn-scores table with GSI for risk level queries."""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "account_id", "KeyType": "HASH"},  # Partition key
                {"AttributeName": "score_date", "KeyType": "RANGE"},  # Sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "account_id", "AttributeType": "S"},
                {"AttributeName": "score_date", "AttributeType": "S"},
                {"AttributeName": "risk_level", "AttributeType": "S"},
                {"AttributeName": "churn_probability", "AttributeType": "N"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "risk-level-index",
                    "KeySchema": [
                        {"AttributeName": "risk_level", "KeyType": "HASH"},
                        {"AttributeName": "churn_probability", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            BillingMode="PAY_PER_REQUEST",  # On-demand billing
        )

        # Wait for table to be created
        table.wait_until_exists()
        print(f"✓ Created table: {table_name}")
        return table

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"⚠ Table {table_name} already exists")
            return dynamodb.Table(table_name)
        else:
            print(f"✗ Failed to create table {table_name}: {e}")
            raise


def create_churn_events_table(dynamodb, table_name: str = "churn-events"):
    """Create churn-events table with GSI for category queries."""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "event_id", "KeyType": "HASH"},  # Partition key
            ],
            AttributeDefinitions=[
                {"AttributeName": "event_id", "AttributeType": "S"},
                {"AttributeName": "churn_reason_category", "AttributeType": "S"},
                {"AttributeName": "churn_date", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "category-date-index",
                    "KeySchema": [
                        {"AttributeName": "churn_reason_category", "KeyType": "HASH"},
                        {"AttributeName": "churn_date", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        table.wait_until_exists()
        print(f"✓ Created table: {table_name}")
        return table

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"⚠ Table {table_name} already exists")
            return dynamodb.Table(table_name)
        else:
            print(f"✗ Failed to create table {table_name}: {e}")
            raise


def create_model_metadata_table(dynamodb, table_name: str = "model-metadata"):
    """Create model-metadata table."""
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "model_version", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "model_version", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        table.wait_until_exists()
        print(f"✓ Created table: {table_name}")
        return table

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"⚠ Table {table_name} already exists")
            return dynamodb.Table(table_name)
        else:
            print(f"✗ Failed to create table {table_name}: {e}")
            raise


def main():
    """Create all DynamoDB tables."""
    print("Creating DynamoDB tables for churn prediction system...")

    # Get region from environment or use default
    import os

    region = os.getenv("AWS_REGION", "us-east-1")

    print(f"Using region: {region}")

    try:
        dynamodb = boto3.resource("dynamodb", region_name=region)

        # Create tables
        create_churn_scores_table(dynamodb)
        create_churn_events_table(dynamodb)
        create_model_metadata_table(dynamodb)

        print("\n✓ All tables created successfully!")
        print("\nTable Summary:")
        print("- churn-scores: Stores customer churn probabilities")
        print("- churn-events: Stores historical churn events")
        print("- model-metadata: Stores ML model versions and metrics")

        return 0

    except Exception as e:
        print(f"\n✗ Error creating tables: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
