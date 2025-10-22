#!/bin/bash
# Deploy Lambda function for ML scoring pipeline

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

echo "Deploying Lambda function: ${LAMBDA_FUNCTION_NAME}"

# Create deployment package
echo "Creating deployment package..."
cd lambda/scoring_pipeline

# Create package directory
rm -rf package deployment.zip
mkdir -p package

# Install dependencies
pip install -r requirements.txt -t package/

# Copy source code
cp -r ../../src/churn_predictor package/
cp handler.py package/

# Create zip
cd package
zip -r ../deployment.zip . > /dev/null
cd ..

echo "✓ Created deployment package ($(du -h deployment.zip | cut -f1))"

# Upload to Lambda or S3 (if package > 50MB)
PACKAGE_SIZE=$(stat -f%z "deployment.zip" 2>/dev/null || stat -c%s "deployment.zip")

if [ $PACKAGE_SIZE -gt 52428800 ]; then
    echo "Package too large for direct upload, using S3..."
    aws s3 cp deployment.zip s3://${S3_DATA_BUCKET}/lambda/deployment.zip

    aws lambda update-function-code \
        --function-name ${LAMBDA_FUNCTION_NAME} \
        --s3-bucket ${S3_DATA_BUCKET} \
        --s3-key lambda/deployment.zip
else
    echo "Uploading directly to Lambda..."
    aws lambda update-function-code \
        --function-name ${LAMBDA_FUNCTION_NAME} \
        --zip-file fileb://deployment.zip
fi

# Update environment variables
echo "Updating environment variables..."
aws lambda update-function-configuration \
    --function-name ${LAMBDA_FUNCTION_NAME} \
    --environment "Variables={\
DYNAMODB_SCORES_TABLE=${DYNAMODB_SCORES_TABLE},\
S3_MODEL_BUCKET=${S3_MODEL_BUCKET},\
MODEL_S3_KEY=${MODEL_S3_KEY},\
AWS_REGION=${AWS_REGION}\
}" \
    --memory-size ${LAMBDA_MEMORY_SIZE:-3008} \
    --timeout ${LAMBDA_TIMEOUT:-900}

echo "✓ Lambda function deployed successfully"

cd ../..
