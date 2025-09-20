# CloudTrail Streamlit Chatbot - ECS Deployment

## Start from here: 
https://medium.com/@DataTechBridge/how-i-built-and-deployed-a-strands-agent-on-ecs-to-diagnose-aws-issues-using-cloudtrail-38e6f7eac634


This folder contains everything needed to deploy the CloudTrail Streamlit Chatbot on AWS ECS using Fargate.

## Quick Start

**For immediate deployment:**

1. **Build and push Docker image:**
   ```bash
   # Windows
   .\build_and_push.ps1
   
   # Linux/Mac
   chmod +x build_and_push.sh && ./build_and_push.sh
   ```

2. **Deploy infrastructure:**
   ```bash
   aws cloudformation create-stack \
     --stack-name cloudtrail-streamlit-stack \
     --template-body file://ecs-cloudtrail-streamlit-stack.yaml \
     --parameters ParameterKey=VpcId,ParameterValue=vpc-your-vpc-id \
                  ParameterKey=SubnetId,ParameterValue=subnet-your-subnet-id \
                  ParameterKey=S3BucketName,ParameterValue=your-athena-bucket \
                  ParameterKey=AthenaResultsBucket,ParameterValue=your-athena-bucket \
                  ParameterKey=ImageTag,ParameterValue=latest \
     --capabilities CAPABILITY_NAMED_IAM \
     --region us-west-2
   ```

3. **Get task public IP:**
   ```bash
   # Get the task ARN
   TASK_ARN=$(aws ecs list-tasks --cluster CloudTrailStreamlitCluster --query 'taskArns[0]' --output text)
   
   # Get the public IP
   aws ecs describe-tasks --cluster CloudTrailStreamlitCluster --tasks $TASK_ARN \
     --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text | \
     xargs -I {} aws ec2 describe-network-interfaces --network-interface-ids {} \
     --query 'NetworkInterfaces[0].Association.PublicIp' --output text
   ```

## Architecture

```
Internet → ECS Fargate (Public IP) → Streamlit App → AWS Bedrock/Athena/Glue
```

## Files Structure

```
cloudtrail-streamlit-ecs-deployment/
├── Project/
│   ├── Dockerfile                    # Container definition
│   ├── requirements.txt              # Python dependencies
│   ├── streamlit_cloudtrail_chatbot.py  # Main Streamlit app
│   └── text_to_sql_agent.py         # CloudTrail agent
├── docs/                            # Documentation (ignored by git)
├── ecs-cloudtrail-streamlit-stack.yaml  # CloudFormation template
├── build_and_push.ps1               # PowerShell build script (Windows)
├── build_and_push.sh                # Bash build script (Linux/Mac)
├── deploy-example.ps1               # Example deployment script (Windows)
├── deploy-example.sh                # Example deployment script (Linux/Mac)
├── run_local.ps1                    # Local testing script (Windows)
├── run_local.sh                     # Local testing script (Linux/Mac)
├── .gitignore                       # Git ignore file
└── README.md                        # This file
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Docker** installed and running
3. **PowerShell** (for Windows) or **Bash** (for Linux/Mac)
4. **Existing AWS Resources**:
   - VPC with public subnet
   - S3 bucket for Athena query results
   - CloudTrail logs in Glue catalog (database and table)
5. **AWS Permissions** for:
   - ECR (Elastic Container Registry)
   - ECS (Elastic Container Service)
   - CloudFormation
   - IAM (for creating roles)
   - VPC/EC2 (for networking)
   - CloudWatch Logs
   - Amazon Bedrock (Claude models)
   - Amazon Athena
   - AWS Glue
   - S3 (for Athena query results)

## Deployment Steps

### Step 1: Build and Push Docker Image

**For Windows (PowerShell):**
```powershell
cd cloudtrail-streamlit-ecs-deployment
.\build_and_push.ps1
```

**For Linux/Mac (Bash):**
```bash
cd cloudtrail-streamlit-ecs-deployment
chmod +x build_and_push.sh
./build_and_push.sh
```

**With custom parameters:**
```bash
# Windows PowerShell
.\build_and_push.ps1 -ECR_REPOSITORY_NAME "my-repo" -IMAGE_TAG "v1.0" -AWS_REGION "us-east-1"

# Linux/Mac Bash
./build_and_push.sh "my-repo" "v1.0" "us-east-1"
```

This script will:
- Create ECR repository if it doesn't exist
- Build the Docker image
- Tag and push to ECR
- Display the image URI

### Step 2: Deploy CloudFormation Stack

**⚠️ Important**: Update the template parameters for your VPC and subnet:

**⚠️ Important**: All parameters are now required (no defaults).

**Required parameters deployment:**
```bash
aws cloudformation create-stack \
  --stack-name cloudtrail-streamlit-stack \
  --template-body file://ecs-cloudtrail-streamlit-stack.yaml \
  --parameters ParameterKey=VpcId,ParameterValue=vpc-your-vpc-id \
               ParameterKey=SubnetId,ParameterValue=subnet-your-subnet-id \
               ParameterKey=S3BucketName,ParameterValue=your-athena-bucket \
               ParameterKey=AthenaResultsBucket,ParameterValue=your-athena-bucket \
               ParameterKey=ImageTag,ParameterValue=latest \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

**Full parameters example:**
```bash
aws cloudformation create-stack \
  --stack-name cloudtrail-streamlit-stack \
  --template-body file://ecs-cloudtrail-streamlit-stack.yaml \
  --parameters ParameterKey=VpcId,ParameterValue=vpc-12345678 \
               ParameterKey=SubnetId,ParameterValue=subnet-12345678 \
               ParameterKey=S3BucketName,ParameterValue=my-athena-bucket \
               ParameterKey=AthenaResultsBucket,ParameterValue=my-athena-bucket \
               ParameterKey=ImageName,ParameterValue=cloudtrail-streamlit-chatbot \
               ParameterKey=ImageTag,ParameterValue=v6.0 \
               ParameterKey=DatabaseName,ParameterValue=logs_database \
               ParameterKey=TableName,ParameterValue=cloudtrail_logs_pp_y_m_d \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

**Or use the example scripts:**
```bash
# Edit values in deploy-example.sh then run:
chmod +x deploy-example.sh && ./deploy-example.sh

# Or PowerShell:
.\deploy-example.ps1
```

### Step 3: Monitor Deployment

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name cloudtrail-streamlit-stack

# Watch stack events
aws cloudformation describe-stack-events --stack-name cloudtrail-streamlit-stack
```

### Step 4: Get Application Access

**Get task public IP:**
```bash
# Method 1: Using task ARN
TASK_ARN=$(aws ecs list-tasks --cluster CloudTrailStreamlitCluster --query 'taskArns[0]' --output text)
aws ecs describe-tasks --cluster CloudTrailStreamlitCluster --tasks $TASK_ARN \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text | \
  xargs -I {} aws ec2 describe-network-interfaces --network-interface-ids {} \
  --query 'NetworkInterfaces[0].Association.PublicIp' --output text
```

**Access the application:**
```bash
# Once you have the IP, access via:
# http://YOUR_PUBLIC_IP
```

**Get stack outputs:**
```bash
# View all stack outputs
aws cloudformation describe-stacks \
  --stack-name cloudtrail-streamlit-stack \
  --query 'Stacks[0].Outputs'
```

## What Gets Created

### Infrastructure Components

1. **VPC & Networking**
   - Uses existing VPC and subnet (specified in parameters)
   - ECS tasks get public IP addresses
   - Security group allows HTTP traffic on port 80

2. **ECS Resources**
   - ECS Cluster (Fargate)
   - Task Definition
   - ECS Service
   - Security Groups

3. **Direct Access**
   - ECS tasks with public IP addresses
   - No load balancer (direct access to tasks)
   - HTTP access on port 80

4. **IAM Roles**
   - ECS Task Role with permissions for:
     - AWS Bedrock (Claude models)
     - Amazon Athena
     - AWS Glue
     - S3 (for Athena results)

5. **CloudWatch**
   - Log Group for container logs

## Configuration

### Environment Variables

The following environment variables are automatically set in the container:

**Required (set by CloudFormation parameters):**
- `AWS_DEFAULT_REGION`: AWS region
- `DATABASE_NAME`: Glue database name (from parameter)
- `TABLE_NAME`: Glue table name (from parameter)
- `ATHENA_RESULTS_BUCKET`: S3 bucket for query results (from parameter)

**Optional (have defaults):**
- `STRANDS_MODEL_ID`: anthropic.claude-3-sonnet-20240229-v1:0
- `STRANDS_MAX_TOKENS`: 4000
- `STRANDS_TEMPERATURE`: 1.0

### Resource Specifications

- **CPU**: 1024 (1 vCPU)
- **Memory**: 2048 MB (2 GB)
- **Port**: 80 (HTTP)
- **Health Check**: `/_stcore/health`

## Accessing the Application

Once deployed, access the application using the task's public IP:
```
http://YOUR_TASK_PUBLIC_IP
```

**Note**: The application runs directly on ECS Fargate with a public IP, not behind a load balancer.

## Troubleshooting

### Common Issues

1. **Container Won't Start**
   ```bash
   # Check ECS service events
   aws ecs describe-services --cluster CloudTrailStreamlitCluster --services cloudtrail-streamlit-stack-Service
   
   # Check container logs
   aws logs get-log-events --log-group-name /ecs/cloudtrail-streamlit-cloudtrail-streamlit-stack --log-stream-name ecs/cloudtrail-streamlit-container/TASK_ID
   ```

2. **Health Check Failures**
   - Verify Streamlit is running on port 80
   - Check security group allows traffic on port 80
   - Ensure health check path `/_stcore/health` is accessible

3. **Permission Errors**
   - Verify ECS Task Role has required permissions
   - Check if Bedrock model is enabled in your region
   - Ensure S3 bucket exists and is accessible

### Useful Commands

```bash
# List running tasks
aws ecs list-tasks --cluster CloudTrailStreamlitCluster

# Get task details
aws ecs describe-tasks --cluster CloudTrailStreamlitCluster --tasks TASK_ARN

# View logs
aws logs describe-log-streams --log-group-name /ecs/cloudtrail-streamlit-cloudtrail-streamlit-stack

# Update service (after new image push)
aws ecs update-service --cluster CloudTrailStreamlitCluster --service cloudtrail-streamlit-stack-Service --force-new-deployment
```

## Cleanup

To delete all resources:

```bash
aws cloudformation delete-stack --stack-name cloudtrail-streamlit-stack
```

**Monitor deletion:**
```bash
# Watch deletion progress
aws cloudformation describe-stack-events --stack-name cloudtrail-streamlit-stack

# Check deletion status
aws cloudformation describe-stacks --stack-name cloudtrail-streamlit-stack
```

**Manual cleanup (if needed):**
```bash
# Delete ECR repository
aws ecr delete-repository --repository-name cloudtrail-streamlit-chatbot --force

# Remove local Docker images
docker rmi cloudtrail-streamlit-chatbot:latest
```

**Note**: This will delete all resources created by the stack. Your existing VPC, subnets, and S3 buckets will remain unchanged.

## Cost Considerations

- **ECS Fargate**: ~$0.04048 per vCPU per hour + $0.004445 per GB per hour
- **Data Transfer**: Standard AWS data transfer rates apply
- **CloudWatch Logs**: $0.50 per GB ingested
- **Bedrock API**: Pay per token usage
- **Athena**: $5.00 per TB of data scanned

**Estimated Monthly Cost**: ~$30-40 for continuous operation (varies by usage and query frequency)

## Security Notes

- Application runs in public subnets with internet access
- Security groups restrict access to HTTP (port 80) only
- ECS tasks use IAM roles for AWS service access
- No SSH access to containers (managed by Fargate)
- All AWS API calls use IAM permissions (no hardcoded credentials)

## Customization

### Modify Container Resources

Edit the CloudFormation template:
```yaml
Cpu: '2048'      # 2 vCPU
Memory: '4096'   # 4 GB
```

### Change Streamlit Configuration

Edit environment variables in the template:
```yaml
Environment:
  - Name: STRANDS_MODEL_ID
    Value: anthropic.claude-3-haiku-20240307-v1:0  # Different model
  - Name: STRANDS_TEMPERATURE
    Value: '0.5'  # Lower temperature
```

### Add Custom Domain

Add Route 53 and Certificate Manager resources to the CloudFormation template for HTTPS and custom domain support.
