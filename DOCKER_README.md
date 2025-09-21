# Docker Setup for Torob AI Assistant API

This document provides instructions for running the Torob AI Assistant API using Docker.

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   cd torob_ai_assistant
   ```

2. **Set environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Build and run:**
   ```bash
   docker-compose up --build
   ```

4. **Access the API:**
   - API: http://localhost:8000
   - Health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t torob-ai-assistant .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 \
     -e OPENAI_API_KEY="your-api-key" \
     -e OPENAI_BASE_URL="https://turbo.torob.com/v1" \
     torob-ai-assistant
   ```

## Production Deployment

### Using Production Dockerfile

For production deployment, use the optimized multi-stage build:

```bash
# Build production image
docker build -f Dockerfile.prod -t torob-ai-assistant:prod .

# Run production container
docker run -d \
  --name torob-ai-prod \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-api-key" \
  -e OPENAI_BASE_URL="https://turbo.torob.com/v1" \
  -v torob-data:/app/data \
  -v torob-logs:/app/logs \
  --restart unless-stopped \
  torob-ai-assistant:prod
```

### Using Docker Compose for Production

```bash
# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | `trb-6500cd2bb70ff9537a-060b-4f37-a6f7-3917ba6cd53e` | OpenAI API key |
| `OPENAI_BASE_URL` | `https://turbo.torob.com/v1` | OpenAI API base URL |
| `LLM_MODEL` | `gpt-4` | Language model to use |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `FORCE_CONCLUSION_TURN` | `5` | Max conversation turns |

## Docker Commands

### Development

```bash
# Build and run with hot reload
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f torob-ai-api

# Stop services
docker-compose down

# Rebuild without cache
docker-compose build --no-cache
```

### Production

```bash
# Build production image
docker build -f Dockerfile.prod -t torob-ai-assistant:prod .

# Run with volume mounts
docker run -d \
  --name torob-ai-prod \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  torob-ai-assistant:prod

# Check container status
docker ps

# View logs
docker logs -f torob-ai-prod

# Stop container
docker stop torob-ai-prod
docker rm torob-ai-prod
```

## Health Checks

The container includes health checks that verify the API is responding:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' torob-ai-assistant

# Manual health check
curl http://localhost:8000/health
```

## Volume Mounts

- `/app/data` - Database and data files
- `/app/logs` - Application logs

## Networking

The application runs on port 8000 by default. You can map it to a different port:

```bash
docker run -p 8080:8000 torob-ai-assistant
```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   
   # Kill the process
   kill -9 <PID>
   ```

2. **Permission denied:**
   ```bash
   # Fix permissions
   sudo chown -R $USER:$USER .
   ```

3. **Container won't start:**
   ```bash
   # Check logs
   docker logs torob-ai-assistant
   
   # Check container status
   docker ps -a
   ```

4. **API not responding:**
   ```bash
   # Check if container is running
   docker ps
   
   # Check health status
   docker inspect torob-ai-assistant | grep Health
   
   # Test API directly
   curl http://localhost:8000/health
   ```

### Debug Mode

Run container in debug mode:

```bash
docker run -it --rm \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-api-key" \
  torob-ai-assistant \
  /bin/bash
```

## Security Considerations

1. **Use production Dockerfile** for production deployments
2. **Set strong environment variables** and don't commit them to version control
3. **Use secrets management** for sensitive data
4. **Regularly update base images** for security patches
5. **Run as non-root user** (included in production Dockerfile)

## Monitoring

### Logs

```bash
# View real-time logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f torob-ai-api

# View last 100 lines
docker-compose logs --tail=100 torob-ai-api
```

### Resource Usage

```bash
# Check resource usage
docker stats torob-ai-assistant

# Check disk usage
docker system df
```

## Scaling

For horizontal scaling, use a load balancer (nginx, traefik) in front of multiple container instances:

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  torob-ai-api:
    build: .
    deploy:
      replicas: 3
    ports:
      - "8000-8002:8000"
```

```bash
# Scale to 3 instances
docker-compose -f docker-compose.scale.yml up --scale torob-ai-api=3
```
