#!/bin/bash

# Hamravesh Docker Deployment Script
# This script helps deploy to Hamravesh with proper error handling

set -e  # Exit on any error

# Configuration
REGISTRY="registry.hamdocker.ir"
IMAGE_NAME="paryfardnim/torob-ai-shopping-assistant"
TAG="latest"
FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo "🚀 Starting Hamravesh deployment process..."

# Function to retry commands with exponential backoff
retry_with_backoff() {
    local max_attempts=3
    local delay=5
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt of $max_attempts..."
        if "$@"; then
            echo "✅ Command succeeded on attempt $attempt"
            return 0
        else
            echo "❌ Command failed on attempt $attempt"
            if [ $attempt -lt $max_attempts ]; then
                echo "⏳ Waiting $delay seconds before retry..."
                sleep $delay
                delay=$((delay * 2))  # Exponential backoff
            fi
            attempt=$((attempt + 1))
        fi
    done
    
    echo "💥 All attempts failed"
    return 1
}

# Step 1: Build the Docker image
echo "📦 Building Docker image..."
docker build -f Dockerfile.optimized -t $FULL_IMAGE_NAME .

# Step 2: Test the image locally
echo "🧪 Testing image locally..."
docker run --rm -d --name test-container -p 8001:8000 $FULL_IMAGE_NAME
sleep 10

# Test health endpoint
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Local test passed"
    docker stop test-container
else
    echo "❌ Local test failed"
    docker stop test-container
    exit 1
fi

# Step 3: Login to registry (if needed)
echo "🔐 Logging into registry..."
# Uncomment the next line if you need to login
# docker login $REGISTRY

# Step 4: Push with retry mechanism
echo "📤 Pushing image to registry..."
retry_with_backoff docker push $FULL_IMAGE_NAME

echo "🎉 Deployment completed successfully!"
echo "Image: $FULL_IMAGE_NAME"
echo "You can now deploy this image on Hamravesh platform."
