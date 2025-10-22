"""CLI commands for churn prediction."""

import sys
from pathlib import Path
from typing import Optional

from churn_predictor.data.loader import load_csv
from churn_predictor.data.preprocessor import preprocess
from churn_predictor.data.validator import validate_schema
from churn_predictor.models.explainer import explain_predictions
from churn_predictor.models.predictor import predict_churn
from churn_predictor.models.trainer import TrainedModel, train_model
from churn_predictor.storage.local_storage import LocalStorage


def cli() -> int:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_help()
        return 1

    command = sys.argv[1]

    if command == "train":
        return cmd_train()
    elif command == "score":
        return cmd_score()
    elif command == "validate":
        return cmd_validate()
    elif command == "generate-data":
        return cmd_generate_data()
    elif command == "help":
        print_help()
        return 0
    else:
        print(f"Unknown command: {command}")
        print_help()
        return 1


def print_help() -> None:
    """Print CLI help."""
    help_text = """
Churn Predictor CLI

Usage:
  python -m churn_predictor.cli <command> [options]

Commands:
  train          Train a new churn prediction model
  score          Generate churn scores for customers
  validate       Validate a CSV file
  generate-data  Generate synthetic customer data
  help           Show this help message

Examples:
  # Generate synthetic data
  python -m churn_predictor.cli generate-data --output data.csv --customers 1000

  # Train model
  python -m churn_predictor.cli train --data sample-data.csv --output models/model-v1.pkl

  # Generate scores
  python -m churn_predictor.cli score --data sample-data.csv --model models/model-v1.pkl

  # Validate data
  python -m churn_predictor.cli validate --data sample-data.csv
"""
    print(help_text)


def parse_args(required_args: list[str]) -> dict[str, str]:
    """Simple argument parser."""
    args = {}
    i = 2  # Skip program name and command
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            key = sys.argv[i][2:]
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
                args[key] = sys.argv[i + 1]
                i += 2
            else:
                args[key] = "true"
                i += 1
        else:
            i += 1

    # Check required arguments
    missing = [arg for arg in required_args if arg not in args]
    if missing:
        print(f"Error: Missing required arguments: {', '.join(f'--{arg}' for arg in missing)}")
        return {}

    return args


def cmd_train() -> int:
    """Train command."""
    args = parse_args(["data"])
    if not args:
        print("\nUsage: python -m churn_predictor.cli train --data <file> [--output <path>]")
        return 1

    data_file = args["data"]
    output_file = args.get("output", "data/models/model-latest.pkl")

    print(f"Loading data from {data_file}...")
    try:
        df = load_csv(data_file)
        print(f"✓ Loaded {len(df)} customer records")
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return 1

    print("Validating data...")
    try:
        result = validate_schema(df)
        if not result.is_valid:
            print(f"✗ Validation failed:")
            print(result)
            return 1
        print(f"✓ Validation passed")
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  ⚠ {warning}")
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return 1

    print("Preprocessing data...")
    try:
        df_processed = preprocess(df)
        print(f"✓ Preprocessed data with {len(df_processed.columns)} features")
    except Exception as e:
        print(f"✗ Preprocessing failed: {e}")
        return 1

    print("Training model...")
    try:
        trained_model = train_model(df_processed, test_size=0.2)
        print(f"✓ Model trained successfully")
        print(f"  F2 Score: {trained_model.performance_metrics['f2_score']:.3f}")
        print(f"  Precision: {trained_model.performance_metrics['precision']:.3f}")
        print(f"  Recall: {trained_model.performance_metrics['recall']:.3f}")
        print(f"  PR-AUC: {trained_model.performance_metrics['pr_auc']:.3f}")
    except Exception as e:
        print(f"✗ Training failed: {e}")
        return 1

    print(f"Saving model to {output_file}...")
    try:
        trained_model.save(output_file)
        print(f"✓ Model saved successfully")
    except Exception as e:
        print(f"✗ Failed to save model: {e}")
        return 1

    return 0


def cmd_score() -> int:
    """Score command."""
    args = parse_args(["data", "model"])
    if not args:
        print("\nUsage: python -m churn_predictor.cli score --data <file> --model <path> [--output <path>]")
        return 1

    data_file = args["data"]
    model_file = args["model"]
    output_file = args.get("output", "data/scores/latest.csv")

    print(f"Loading model from {model_file}...")
    try:
        trained_model = TrainedModel.load(model_file)
        print(f"✓ Loaded model version {trained_model.version}")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return 1

    print(f"Loading data from {data_file}...")
    try:
        df = load_csv(data_file)
        print(f"✓ Loaded {len(df)} customer records")
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return 1

    print("Preprocessing data...")
    try:
        df_processed = preprocess(df)
        print(f"✓ Preprocessed data")
    except Exception as e:
        print(f"✗ Preprocessing failed: {e}")
        return 1

    print("Generating predictions...")
    try:
        df_predictions = predict_churn(trained_model, df_processed)
        print(f"✓ Generated predictions")

        # Count risk levels
        risk_counts = df_predictions["risk_level"].value_counts()
        print(f"  High risk: {risk_counts.get('high', 0)}")
        print(f"  Medium risk: {risk_counts.get('medium', 0)}")
        print(f"  Low risk: {risk_counts.get('low', 0)}")
    except Exception as e:
        print(f"✗ Prediction failed: {e}")
        return 1

    print("Generating explanations...")
    try:
        df_explained = explain_predictions(trained_model, df_predictions)
        print(f"✓ Generated SHAP explanations")
        df_to_save = df_explained
    except Exception as e:
        print(f"⚠ Warning: Explanation failed: {e}")
        print(f"  Continuing without SHAP explanations...")
        # Add empty risk factors column as fallback
        df_predictions["top_risk_factors"] = [[] for _ in range(len(df_predictions))]
        df_to_save = df_predictions

    print(f"Saving scores to {output_file}...")
    try:
        storage = LocalStorage()
        storage.save_scores(df_to_save, Path(output_file).name)
        print(f"✓ Scores saved successfully")
    except Exception as e:
        print(f"✗ Failed to save scores: {e}")
        return 1

    return 0


def cmd_validate() -> int:
    """Validate command."""
    args = parse_args(["data"])
    if not args:
        print("\nUsage: python -m churn_predictor.cli validate --data <file>")
        return 1

    data_file = args["data"]

    print(f"Loading data from {data_file}...")
    try:
        df = load_csv(data_file)
        print(f"✓ Loaded {len(df)} customer records")
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return 1

    print("Validating data...")
    try:
        result = validate_schema(df)
        print(result)
        return 0 if result.is_valid else 1
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return 1


def cmd_generate_data() -> int:
    """Generate synthetic data command."""
    args = parse_args(["output"])
    if not args:
        print("\nUsage: python -m churn_predictor.cli generate-data --output <file> [--customers <num>] [--churn-rate <rate>]")
        return 1

    output_file = args["output"]
    num_customers = int(args.get("customers", 1000))
    churn_rate = float(args.get("churn-rate", 0.15))

    print(f"Generating synthetic data...")
    print(f"  Customers: {num_customers}")
    print(f"  Churn rate: {churn_rate:.1%}")

    try:
        from churn_predictor.data.synthetic import generate_customer_data

        df = generate_customer_data(
            num_customers=num_customers,
            num_months=12,
            churn_rate=churn_rate,
        )

        print(f"✓ Generated {len(df)} records for {num_customers} customers")

        # Save to CSV
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"✓ Saved to {output_file}")

        # Show statistics
        churned = df[df["churned"] == 1]["account_id"].nunique()
        print(f"\nStatistics:")
        print(f"  Total customers: {num_customers}")
        print(f"  Churned: {churned} ({churned/num_customers:.1%})")
        print(f"  Records: {len(df)}")

        return 0

    except Exception as e:
        print(f"✗ Failed to generate data: {e}")
        import traceback
        traceback.print_exc()
        return 1
