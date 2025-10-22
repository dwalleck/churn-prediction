"""AWS Lambda handler for churn scoring pipeline."""

import json
import os
import tempfile
from pathlib import Path

import boto3

# Add src to path
import sys
sys.path.insert(0, '/opt/python')

from churn_predictor.data.loader import load_csv
from churn_predictor.data.preprocessor import preprocess
from churn_predictor.data.validator import validate_schema
from churn_predictor.models.explainer import explain_predictions
from churn_predictor.models.predictor import predict_churn
from churn_predictor.models.trainer import TrainedModel
from churn_predictor.storage.repositories import ChurnScoreRepository


def lambda_handler(event, context):
    """
    Lambda function triggered by S3 CSV upload.

    Workflow:
    1. Download CSV from S3
    2. Load and validate data
    3. Preprocess features
    4. Load model from S3
    5. Generate predictions
    6. Save to DynamoDB

    Event format:
    {
        "Records": [{
            "s3": {
                "bucket": {"name": "bucket-name"},
                "object": {"key": "uploads/customers.csv"}
            }
        }]
    }
    """
    print(f"Received event: {json.dumps(event)}")

    try:
        # Get S3 event details
        record = event["Records"][0]
        bucket_name = record["s3"]["bucket"]["name"]
        object_key = record["s3"]["object"]["key"]

        print(f"Processing file: s3://{bucket_name}/{object_key}")

        # Initialize AWS clients
        s3 = boto3.client("s3")
        repository = ChurnScoreRepository(
            table_name=os.getenv("DYNAMODB_SCORES_TABLE", "churn-scores")
        )

        # Download CSV to temp file
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            s3.download_file(bucket_name, object_key, tmp_path)
            print(f"Downloaded CSV to {tmp_path}")

        # Load and validate data
        print("Loading CSV...")
        df = load_csv(tmp_path)
        print(f"Loaded {len(df)} records")

        print("Validating schema...")
        validation_result = validate_schema(df)
        if not validation_result.is_valid:
            raise ValueError(f"Validation failed: {validation_result}")
        print("Validation passed")

        # Preprocess
        print("Preprocessing...")
        df_processed = preprocess(df)
        print(f"Preprocessed to {len(df_processed.columns)} features")

        # Load model
        model_path = os.getenv("MODEL_S3_KEY", "models/active/model.pkl")
        model_bucket = os.getenv("S3_MODEL_BUCKET", bucket_name)

        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as tmp_model:
            model_tmp_path = tmp_model.name
            s3.download_file(model_bucket, model_path, model_tmp_path)
            print(f"Downloaded model from s3://{model_bucket}/{model_path}")

        model = TrainedModel.load(model_tmp_path)
        print(f"Loaded model version {model.version}")

        # Generate predictions
        print("Generating predictions...")
        df_predictions = predict_churn(model, df_processed)
        print(f"Generated predictions")

        # Generate explanations (optional, can be skipped for performance)
        try:
            print("Generating explanations...")
            df_explained = explain_predictions(model, df_predictions)
            df_final = df_explained
        except Exception as e:
            print(f"Warning: Explanation failed: {e}, continuing without")
            df_predictions["top_risk_factors"] = [[] for _ in range(len(df_predictions))]
            df_final = df_predictions

        # Save to DynamoDB
        print("Saving to DynamoDB...")
        scores = []
        for _, row in df_final.iterrows():
            score = {
                "account_id": str(row["account_id"]),
                "score_date": str(row.get("month", "")),
                "churn_probability": float(row["churn_probability"]),
                "risk_level": str(row["risk_level"]),
                "confidence": float(row["confidence"]),
                "model_version": model.version,
                "top_risk_factors": row.get("top_risk_factors", []),
            }
            scores.append(score)

        saved_count = repository.save_scores(scores)
        print(f"Saved {saved_count} scores to DynamoDB")

        # Cleanup
        os.unlink(tmp_path)
        os.unlink(model_tmp_path)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Pipeline completed successfully",
                "records_processed": len(df),
                "scores_saved": saved_count,
                "high_risk_count": len(df_final[df_final["risk_level"] == "high"]),
            }),
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
