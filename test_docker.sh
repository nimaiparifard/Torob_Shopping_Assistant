#!/bin/bash

# Test Docker build and run script
# This script tests the complete Docker setup to ensure everything works

set -e  # Exit on any error

echo "🧪 Testing Docker build and run process..."

# Step 1: Clean up previous containers and images
echo "🧹 Cleaning up previous containers and images..."
docker stop torob-ai-container 2>/dev/null || true
docker rm torob-ai-container 2>/dev/null || true
docker rmi torob-ai-assistant 2>/dev/null || true

# Step 2: Remove backup folder to test download process
echo "🗑️ Removing backup folder to test download process..."
rm -rf backup

# Step 3: Build the Docker image
echo "📦 Building Docker image..."
docker build -t torob-ai-assistant .

# Step 4: Run the container and show logs
echo "🚀 Running container..."
echo "This will show the complete startup process including data download..."
echo "Press Ctrl+C to stop the container when you're satisfied it's working"
echo "=========================================="

docker run -p 8000:8000 --name torob-ai-container torob-ai-assistant
