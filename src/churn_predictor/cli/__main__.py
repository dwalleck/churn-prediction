"""CLI entry point for churn predictor."""

import sys
from pathlib import Path

from churn_predictor.cli.commands import cli

if __name__ == "__main__":
    sys.exit(cli())
