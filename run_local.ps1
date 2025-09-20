# Build and run CloudTrail Streamlit app locally
param(
    [string]$ImageName = "cloudtrail-streamlit-local",
    [string]$ContainerName = "cloudtrail-streamlit-container",
    [int]$Port = 8501
)

Write-Host "Building Docker image..." -ForegroundColor Green
docker build -t $ImageName ./Project

if ($LASTEXITCODE -eq 0) {
    Write-Host "Image built successfully!" -ForegroundColor Green
    
    # Stop and remove existing container if it exists
    docker stop $ContainerName 2>$null
    docker rm $ContainerName 2>$null
    
    Write-Host "Starting container on port $Port..." -ForegroundColor Green
    docker run -d `
        --name $ContainerName `
        -p ${Port}:80 `
        -e AWS_DEFAULT_REGION=us-west-2 `
        -e STRANDS_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0 `
        -e STRANDS_MAX_TOKENS=4000 `
        -e STRANDS_TEMPERATURE=1.0 `
        $ImageName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Container started successfully!" -ForegroundColor Green
        Write-Host "Access the app at: http://localhost:$Port" -ForegroundColor Yellow
        Write-Host "Container name: $ContainerName" -ForegroundColor Cyan
        
        Write-Host "`nUseful commands:" -ForegroundColor Magenta
        Write-Host "  View logs: docker logs $ContainerName" -ForegroundColor White
        Write-Host "  Stop container: docker stop $ContainerName" -ForegroundColor White
        Write-Host "  Remove container: docker rm $ContainerName" -ForegroundColor White
    } else {
        Write-Host "Failed to start container!" -ForegroundColor Red
    }
} else {
    Write-Host "Failed to build image!" -ForegroundColor Red
}