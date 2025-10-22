#!/usr/bin/env python
"""Compare multiple trained models and recommend the best."""

import sys
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from churn_predictor.models.trainer import TrainedModel


def compare_models(model_paths: List[str]) -> None:
    """
    Compare multiple models and print metrics.

    Args:
        model_paths: List of paths to trained model files
    """
    print("Loading models...")
    models = []

    for path in model_paths:
        try:
            model = TrainedModel.load(path)
            models.append((path, model))
            print(f"✓ Loaded {path}: {model.version}")
        except Exception as e:
            print(f"✗ Failed to load {path}: {e}")

    if len(models) == 0:
        print("No models loaded successfully")
        return

    print(f"\n{'='*80}")
    print(f"{'Model Comparison':<80}")
    print(f"{'='*80}\n")

    # Print comparison table
    print(f"{'Model':<40} {'Version':<20} {'F2':<8} {'Precision':<12} {'Recall':<8} {'PR-AUC':<8}")
    print("-" * 96)

    best_model = None
    best_f2 = -1

    for path, model in models:
        metrics = model.performance_metrics
        f2 = metrics.get("f2_score", 0)
        precision = metrics.get("precision", 0)
        recall = metrics.get("recall", 0)
        pr_auc = metrics.get("pr_auc", 0)

        print(f"{Path(path).name:<40} {model.version:<20} {f2:<8.3f} {precision:<12.3f} {recall:<8.3f} {pr_auc:<8.3f}")

        if f2 > best_f2:
            best_f2 = f2
            best_model = (path, model)

    print("\n" + "=" * 96)
    print(f"\n🏆 **Best Model**: {Path(best_model[0]).name}")
    print(f"   Version: {best_model[1].version}")
    print(f"   F2 Score: {best_model[1].performance_metrics['f2_score']:.3f}")

    print(f"\n📊 **Top 5 Feature Importance** (from best model):")
    sorted_features = sorted(
        best_model[1].feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    for i, (feature, importance) in enumerate(sorted_features, 1):
        print(f"   {i}. {feature:<30} {importance:.3f}")

    print(f"\n💡 **Recommendation**: Use {Path(best_model[0]).name} for production deployment")


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python scripts/compare_models.py <model1.pkl> <model2.pkl> [model3.pkl ...]")
        print("\nExample:")
        print("  python scripts/compare_models.py data/models/model-v1.pkl data/models/model-v2.pkl")
        return 1

    model_paths = sys.argv[1:]
    compare_models(model_paths)
    return 0


if __name__ == "__main__":
    sys.exit(main())
