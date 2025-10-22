# Dockerfile for Streamlit dashboard on AWS Fargate

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml /app/

# Install Python dependencies
RUN pip install --no-cache-dir \
    xgboost>=3.0.0 \
    scikit-learn>=1.3.0 \
    pandas>=2.1.0 \
    numpy>=1.26.0 \
    streamlit>=1.28.0 \
    plotly>=5.17.0 \
    boto3>=1.28.0 \
    shap>=0.43.0

# Copy source code
COPY src/ /app/src/
COPY .streamlit/ /app/.streamlit/

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
