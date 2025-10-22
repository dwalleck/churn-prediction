#!/bin/bash
# Deploy Streamlit dashboard to AWS Fargate

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

echo "Deploying dashboard to AWS Fargate"

# Build Docker image
echo "Building Docker image..."
docker build -t ${ECR_REPOSITORY}:latest .

# Get ECR login
echo "Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
    docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Tag and push image
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"
docker tag ${ECR_REPOSITORY}:latest ${ECR_URI}:latest
docker tag ${ECR_REPOSITORY}:latest ${ECR_URI}:$(date +%Y%m%d%H%M%S)

echo "Pushing image to ECR..."
docker push ${ECR_URI}:latest

# Update ECS service
echo "Updating ECS service..."
aws ecs update-service \
    --cluster ${ECS_CLUSTER_NAME} \
    --service ${ECS_SERVICE_NAME} \
    --force-new-deployment

echo "✓ Dashboard deployed successfully"
echo "Service will be available shortly at the ALB endpoint"
