#!/bin/bash

# Example deployment script with all required parameters
# Update these values for your environment

VPC_ID="vpc-your-vpc-id"
SUBNET_ID="subnet-your-subnet-id"
S3_BUCKET="your-athena-results-bucket"
IMAGE_NAME="cloudtrail-streamlit-chatbot"
IMAGE_TAG="latest"
DATABASE_NAME="logs_database"
TABLE_NAME="cloudtrail_logs_pp_y_m_d"
STACK_NAME="cloudtrail-streamlit-stack"
REGION="us-west-2"

echo "Deploying CloudTrail Streamlit Stack..."
echo "VPC: $VPC_ID"
echo "Subnet: $SUBNET_ID"
echo "S3 Bucket: $S3_BUCKET"
echo "Image: $IMAGE_NAME:$IMAGE_TAG"

aws cloudformation create-stack \
  --stack-name $STACK_NAME \
  --template-body file://ecs-cloudtrail-streamlit-stack.yaml \
  --parameters \
    ParameterKey=VpcId,ParameterValue=$VPC_ID \
    ParameterKey=SubnetId,ParameterValue=$SUBNET_ID \
    ParameterKey=S3BucketName,ParameterValue=$S3_BUCKET \
    ParameterKey=AthenaResultsBucket,ParameterValue=$S3_BUCKET \
    ParameterKey=ImageName,ParameterValue=$IMAGE_NAME \
    ParameterKey=ImageTag,ParameterValue=$IMAGE_TAG \
    ParameterKey=DatabaseName,ParameterValue=$DATABASE_NAME \
    ParameterKey=TableName,ParameterValue=$TABLE_NAME \
  --capabilities CAPABILITY_NAMED_IAM \
  --region $REGION

echo "Stack deployment initiated. Monitor with:"
echo "aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION"