#!/bin/bash

# Build and run CloudTrail Streamlit app locally
IMAGE_NAME=${1:-"cloudtrail-streamlit-local"}
CONTAINER_NAME=${2:-"cloudtrail-streamlit-container"}
PORT=${3:-8501}

echo "Building Docker image..."
docker build -t $IMAGE_NAME ./Project

if [ $? -eq 0 ]; then
    echo "Image built successfully!"
    
    # Stop and remove existing container if it exists
    docker stop $CONTAINER_NAME 2>/dev/null
    docker rm $CONTAINER_NAME 2>/dev/null
    
    echo "Starting container on port $PORT..."
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:80 \
        -e AWS_DEFAULT_REGION=us-west-2 \
        -e STRANDS_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0 \
        -e STRANDS_MAX_TOKENS=4000 \
        -e STRANDS_TEMPERATURE=1.0 \
        $IMAGE_NAME
    
    if [ $? -eq 0 ]; then
        echo "Container started successfully!"
        echo "Access the app at: http://localhost:$PORT"
        echo "Container name: $CONTAINER_NAME"
        
        echo ""
        echo "Useful commands:"
        echo "  View logs: docker logs $CONTAINER_NAME"
        echo "  Stop container: docker stop $CONTAINER_NAME"
        echo "  Remove container: docker rm $CONTAINER_NAME"
    else
        echo "Failed to start container!"
        exit 1
    fi
else
    echo "Failed to build image!"
    exit 1
fi