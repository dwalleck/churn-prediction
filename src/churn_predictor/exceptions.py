"""Custom exceptions for the churn prediction system."""


class ChurnPredictorError(Exception):
    """Base exception for all churn predictor errors."""

    pass


class ValidationError(ChurnPredictorError):
    """Raised when data validation fails."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}


class ModelError(ChurnPredictorError):
    """Raised when model training or prediction fails."""

    def __init__(self, message: str, model_version: str | None = None):
        super().__init__(message)
        self.model_version = model_version


class StorageError(ChurnPredictorError):
    """Raised when storage operations (S3, DynamoDB) fail."""

    def __init__(self, message: str, resource: str | None = None):
        super().__init__(message)
        self.resource = resource
