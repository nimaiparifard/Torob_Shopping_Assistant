#!/bin/bash

# Docker build script for Torob AI Assistant API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BUILD_TYPE="dev"
IMAGE_NAME="torob-ai-assistant"
TAG="latest"
PUSH=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE     Build type: dev (default) or prod"
    echo "  -n, --name NAME     Image name (default: torob-ai-assistant)"
    echo "  -g, --tag TAG       Image tag (default: latest)"
    echo "  -p, --push          Push image to registry after build"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Build development image"
    echo "  $0 -t prod -g v1.0.0                 # Build production image with tag"
    echo "  $0 -t prod -g v1.0.0 -p              # Build and push production image"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -g|--tag)
            TAG="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate build type
if [[ "$BUILD_TYPE" != "dev" && "$BUILD_TYPE" != "prod" ]]; then
    print_error "Invalid build type: $BUILD_TYPE. Must be 'dev' or 'prod'"
    exit 1
fi

# Set Dockerfile based on build type
if [[ "$BUILD_TYPE" == "prod" ]]; then
    DOCKERFILE="Dockerfile.prod"
    print_status "Building production image..."
else
    DOCKERFILE="Dockerfile"
    print_status "Building development image..."
fi

# Full image name
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

print_status "Build configuration:"
echo "  Type: $BUILD_TYPE"
echo "  Dockerfile: $DOCKERFILE"
echo "  Image: $FULL_IMAGE_NAME"
echo "  Push: $PUSH"
echo ""

# Check if Dockerfile exists
if [[ ! -f "$DOCKERFILE" ]]; then
    print_error "Dockerfile not found: $DOCKERFILE"
    exit 1
fi

# Build the image
print_status "Building Docker image..."
if docker build -f "$DOCKERFILE" -t "$FULL_IMAGE_NAME" .; then
    print_success "Docker image built successfully: $FULL_IMAGE_NAME"
else
    print_error "Failed to build Docker image"
    exit 1
fi

# Show image details
print_status "Image details:"
docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# Push image if requested
if [[ "$PUSH" == true ]]; then
    print_status "Pushing image to registry..."
    if docker push "$FULL_IMAGE_NAME"; then
        print_success "Image pushed successfully: $FULL_IMAGE_NAME"
    else
        print_error "Failed to push image"
        exit 1
    fi
fi

print_success "Build completed successfully!"

# Show run commands
echo ""
print_status "To run the container:"
echo "  docker run -p 8000:8000 $FULL_IMAGE_NAME"
echo ""
print_status "To run with environment variables:"
echo "  docker run -p 8000:8000 -e OPENAI_API_KEY='your-key' $FULL_IMAGE_NAME"
echo ""
print_status "To run with docker-compose:"
echo "  docker-compose up"
