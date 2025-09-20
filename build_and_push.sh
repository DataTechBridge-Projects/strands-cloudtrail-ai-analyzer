#!/bin/bash

# Parameters
ECR_REPOSITORY_NAME=${1:-"cloudtrail-streamlit-chatbot"}
IMAGE_TAG=${2:-"latest"}
AWS_REGION=${3:-"us-west-2"}

echo "Building and pushing CloudTrail Streamlit Chatbot to ECR..."

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: Unable to get AWS Account ID. Please check your AWS credentials."
    exit 1
fi

echo "Repository: $ECR_REPOSITORY_NAME"
echo "Tag: $IMAGE_TAG"
echo "Region: $AWS_REGION"
echo "Account ID: $AWS_ACCOUNT_ID"

# Create ECR repository if it does not exist
echo "Creating ECR repository if it does not exist..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION > /dev/null 2>&1
if [ $? -ne 0 ]; then
    aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION
fi

# Authenticate Docker to ECR
echo "Authenticating Docker to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Change to Project directory
cd Project

# Build Docker image
echo "Building Docker image..."
docker build -t "${ECR_REPOSITORY_NAME}:${IMAGE_TAG}" .

# Tag image for ECR
echo "Tagging image for ECR..."
docker tag "${ECR_REPOSITORY_NAME}:${IMAGE_TAG}" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${ECR_REPOSITORY_NAME}:${IMAGE_TAG}"

# Push image to ECR
echo "Pushing image to ECR..."
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${ECR_REPOSITORY_NAME}:${IMAGE_TAG}"

# Return to parent directory
cd ..

echo "✅ Image pushed successfully to $ECR_REPOSITORY_NAME"
echo "📋 Image URI: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/${ECR_REPOSITORY_NAME}:${IMAGE_TAG}"
echo "🚀 Ready to deploy with CloudFormation!"
echo "Use the following command to deploy:"
echo "aws cloudformation create-stack --stack-name cloudtrail-streamlit-stack --template-body file://ecs-cloudtrail-streamlit-stack.yaml --capabilities CAPABILITY_NAMED_IAM --region us-west-2"