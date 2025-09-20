# ✅ Deployment Checklist

## Before You Deploy

### Required AWS Resources (must exist):
- [ ] VPC with public subnet
- [ ] S3 bucket for Athena query results
- [ ] CloudTrail logs configured in AWS Glue
  - [ ] Database: `logs_database` (or your custom name)
  - [ ] Table: `cloudtrail_logs_pp_y_m_d` (or your custom name)

### Required Information:
- [ ] VPC ID (e.g., vpc-12345678)
- [ ] Public Subnet ID (e.g., subnet-12345678)
- [ ] S3 Bucket Name for Athena results
- [ ] AWS Region where you want to deploy

### AWS Permissions Required:
- [ ] ECR: Create repositories, push images
- [ ] ECS: Create clusters, services, tasks
- [ ] CloudFormation: Create/update stacks
- [ ] IAM: Create roles and policies
- [ ] Bedrock: Access to Claude models
- [ ] Athena: Query execution permissions
- [ ] Glue: Read catalog permissions
- [ ] S3: Read/write to results bucket

## Deployment Steps

### 1. Build and Push Image
```bash
# Windows
.\build_and_push.ps1 -IMAGE_TAG "v6.0"

# Linux/Mac
./build_and_push.sh cloudtrail-streamlit-chatbot v6.0 us-west-2
```

### 2. Deploy Stack
```bash
# Use example script (recommended)
.\deploy-example.ps1  # Windows
./deploy-example.sh   # Linux/Mac

# Or manual deployment with all parameters
aws cloudformation create-stack \
  --stack-name cloudtrail-streamlit-stack \
  --template-body file://ecs-cloudtrail-streamlit-stack.yaml \
  --parameters \
    ParameterKey=VpcId,ParameterValue=vpc-YOUR-VPC-ID \
    ParameterKey=SubnetId,ParameterValue=subnet-YOUR-SUBNET-ID \
    ParameterKey=AthenaResultsBucket,ParameterValue=YOUR-S3-BUCKET \
    ParameterKey=ImageTag,ParameterValue=v6.0 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

### 3. Get Application URL
```bash
# Get task public IP
TASK_ARN=$(aws ecs list-tasks --cluster CloudTrailStreamlitCluster --query 'taskArns[0]' --output text)
aws ecs describe-tasks --cluster CloudTrailStreamlitCluster --tasks $TASK_ARN \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text | \
  xargs -I {} aws ec2 describe-network-interfaces --network-interface-ids {} \
  --query 'NetworkInterfaces[0].Association.PublicIp' --output text
```

## Verification

### Check Deployment Status:
```bash
aws cloudformation describe-stacks --stack-name cloudtrail-streamlit-stack --region us-west-2
```

### Test Application:
- [ ] Access http://YOUR-PUBLIC-IP
- [ ] Try example query: "Show me S3 activity today"
- [ ] Verify agent responds with SQL and results

## Troubleshooting

### Common Issues:
1. **Stack creation fails**: Check all required parameters are provided
2. **Container won't start**: Verify S3 bucket exists and is accessible
3. **Agent errors**: Ensure Bedrock model access is enabled in your region
4. **No data returned**: Verify CloudTrail logs exist in specified Glue table

### Useful Commands:
```bash
# View container logs
aws logs get-log-events --log-group-name /ecs/cloudtrail-streamlit-cloudtrail-streamlit-stack --log-stream-name ecs/cloudtrail-streamlit-container/TASK_ID

# Force new deployment after image update
aws ecs update-service --cluster CloudTrailStreamlitCluster --service cloudtrail-streamlit-stack-Service --force-new-deployment
```