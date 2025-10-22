"""AWS storage repositories for DynamoDB and S3."""

import json
from datetime import datetime
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

from churn_predictor.exceptions import StorageError


class ChurnScoreRepository:
    """Repository for churn scores in DynamoDB."""

    def __init__(self, table_name: str = "churn-scores", region: str = "us-east-1"):
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)

    def save_scores(self, scores: list[dict[str, Any]]) -> int:
        """
        Save churn scores to DynamoDB with batch writing.

        Args:
            scores: List of score dictionaries

        Returns:
            Number of scores saved

        Raises:
            StorageError: If save fails
        """
        try:
            with self.table.batch_writer() as batch:
                for score in scores:
                    batch.put_item(Item=score)
            return len(scores)
        except ClientError as e:
            raise StorageError(
                f"Failed to save scores to DynamoDB: {e.response['Error']['Message']}",
                resource=self.table_name,
            )

    def get_score(self, account_id: str, score_date: Optional[str] = None) -> Optional[dict]:
        """Get churn score for a customer."""
        try:
            if score_date:
                response = self.table.get_item(
                    Key={"account_id": account_id, "score_date": score_date}
                )
            else:
                # Get latest score
                response = self.table.query(
                    KeyConditionExpression="account_id = :aid",
                    ExpressionAttributeValues={":aid": account_id},
                    ScanIndexForward=False,
                    Limit=1,
                )
                return response["Items"][0] if response["Items"] else None

            return response.get("Item")

        except ClientError as e:
            raise StorageError(
                f"Failed to get score: {e.response['Error']['Message']}",
                resource=self.table_name,
            )

    def get_high_risk_customers(
        self, risk_level: str = "high", limit: int = 100
    ) -> list[dict]:
        """Get high-risk customers using GSI."""
        try:
            response = self.table.query(
                IndexName="risk-level-index",
                KeyConditionExpression="risk_level = :level",
                ExpressionAttributeValues={":level": risk_level},
                ScanIndexForward=False,
                Limit=limit,
            )
            return response.get("Items", [])

        except ClientError as e:
            raise StorageError(
                f"Failed to query high-risk customers: {e.response['Error']['Message']}",
                resource=self.table_name,
            )


class ModelRepository:
    """Repository for ML models in S3."""

    def __init__(self, bucket_name: str = "churn-models", region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.s3 = boto3.client("s3", region_name=region)

    def save_model(self, model_path: str, s3_key: str) -> str:
        """
        Upload model to S3.

        Args:
            model_path: Local path to model file
            s3_key: S3 object key

        Returns:
            S3 URI

        Raises:
            StorageError: If upload fails
        """
        try:
            self.s3.upload_file(model_path, self.bucket_name, s3_key)
            return f"s3://{self.bucket_name}/{s3_key}"

        except ClientError as e:
            raise StorageError(
                f"Failed to upload model to S3: {e.response['Error']['Message']}",
                resource=self.bucket_name,
            )

    def get_active_model(self) -> str:
        """
        Get path to active model.

        Returns:
            S3 URI of active model
        """
        # In production, this would query metadata table
        # For now, return a default path
        return f"s3://{self.bucket_name}/models/active/model.pkl"

    def list_models(self, prefix: str = "models/") -> list[str]:
        """List all models in S3."""
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]

        except ClientError as e:
            raise StorageError(
                f"Failed to list models: {e.response['Error']['Message']}",
                resource=self.bucket_name,
            )


class ChurnEventRepository:
    """Repository for churn events in DynamoDB."""

    def __init__(self, table_name: str = "churn-events", region: str = "us-east-1"):
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)

    def save_events(self, events: list[dict[str, Any]]) -> int:
        """Save churn events to DynamoDB."""
        try:
            with self.table.batch_writer() as batch:
                for event in events:
                    batch.put_item(Item=event)
            return len(events)

        except ClientError as e:
            raise StorageError(
                f"Failed to save churn events: {e.response['Error']['Message']}",
                resource=self.table_name,
            )

    def get_churn_events(
        self,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[dict]:
        """Get churn events with optional filtering."""
        try:
            if category:
                response = self.table.query(
                    IndexName="category-date-index",
                    KeyConditionExpression="churn_reason_category = :cat",
                    ExpressionAttributeValues={":cat": category},
                )
            else:
                response = self.table.scan()

            events = response.get("Items", [])

            # Filter by date if provided
            if start_date or end_date:
                filtered = []
                for event in events:
                    event_date = event.get("churn_date", "")
                    if start_date and event_date < start_date:
                        continue
                    if end_date and event_date > end_date:
                        continue
                    filtered.append(event)
                events = filtered

            return events

        except ClientError as e:
            raise StorageError(
                f"Failed to get churn events: {e.response['Error']['Message']}",
                resource=self.table_name,
            )
