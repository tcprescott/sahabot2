# Docker Quick Start Guide

This guide helps you test the Docker build locally before deploying to Kubernetes.

## Prerequisites

- Docker installed and running
- Digital Ocean account (for testing with actual registry)
- `.env` file configured (copy from `.env.example`)

## Local Testing

### 1. Build the Docker Image

```bash
# Build the image
docker build -t sahabot2:local .

# Or build with a specific tag
docker build -t sahabot2:v1.0.0 .
```

### 2. Run Locally with Docker

#### Option A: Using Docker with .env file

```bash
# Run with environment file
docker run -d \
  --name sahabot2 \
  --env-file .env \
  -p 8080:8080 \
  sahabot2:local
```

#### Option B: Using Docker Compose (recommended for local development)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    env_file:
      - .env
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME}
      MYSQL_USER: ${DB_USER}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    restart: unless-stopped

volumes:
  mysql_data:
```

Then run:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Test the Application

```bash
# Check if container is running
docker ps

# View logs
docker logs sahabot2 -f

# Check health endpoint
curl http://localhost:8080/api/health

# Access the application
# Open browser to http://localhost:8080
```

### 4. Execute Commands in Container

```bash
# Get a shell in the container
docker exec -it sahabot2 /bin/bash

# Run database migrations
docker exec sahabot2 poetry run aerich upgrade

# Check Python version
docker exec sahabot2 python --version
```

## Push to Digital Ocean Registry

### 1. Authenticate with Digital Ocean

```bash
# Install doctl if not already installed
# macOS: brew install doctl
# Linux: snap install doctl

# Authenticate
doctl auth init

# Login to registry
doctl registry login
```

### 2. Tag and Push

```bash
# Tag for your registry
docker tag sahabot2:local registry.digitalocean.com/YOUR_REGISTRY_NAME/sahabot2:latest

# Or with version tag
docker tag sahabot2:local registry.digitalocean.com/YOUR_REGISTRY_NAME/sahabot2:v1.0.0

# Push to registry
docker push registry.digitalocean.com/YOUR_REGISTRY_NAME/sahabot2:latest
docker push registry.digitalocean.com/YOUR_REGISTRY_NAME/sahabot2:v1.0.0
```

### 3. Verify Upload

```bash
# List images in registry
doctl registry repository list-v2

# List tags for specific repository
doctl registry repository list-tags sahabot2
```

## Troubleshooting

### Build Fails

**Error: Poetry lock file not found**
- Ensure `poetry.lock` exists in the repository
- Run `poetry install` locally first

**Error: Dependencies fail to install**
- Check that all system dependencies are in Dockerfile
- Verify Poetry version matches your local version

### Container Won't Start

**Check logs:**
```bash
docker logs sahabot2
```

**Common issues:**
- Missing environment variables - check `.env` file
- Database connection failure - ensure DB is running
- Port already in use - change port mapping: `-p 8081:8080`

### Database Connection Issues

**If using external database:**
```bash
# Test connection from container
docker exec sahabot2 ping -c 3 your-db-host
```

**If using Docker Compose:**
```bash
# Check if MySQL is ready
docker-compose exec db mysql -u$DB_USER -p$DB_PASSWORD -e "SHOW DATABASES;"
```

### Permission Issues

**If you get permission errors:**
```bash
# Container runs as user 1000 (non-root for security)
# Ensure mounted volumes have correct permissions
sudo chown -R 1000:1000 ./data
```

## Multi-Platform Builds

To build for multiple architectures (e.g., ARM for Apple Silicon):

```bash
# Set up buildx (one time)
docker buildx create --use

# Build multi-platform image
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t registry.digitalocean.com/YOUR_REGISTRY_NAME/sahabot2:latest \
  --push \
  .
```

## Clean Up

```bash
# Stop and remove container
docker stop sahabot2
docker rm sahabot2

# Remove image
docker rmi sahabot2:local

# Remove all unused images
docker system prune -a

# If using Docker Compose
docker-compose down -v  # -v also removes volumes
```

## Performance Tips

1. **Use BuildKit**: Enable for faster builds
   ```bash
   export DOCKER_BUILDKIT=1
   docker build -t sahabot2:local .
   ```

2. **Cache Dependencies**: The Dockerfile is already optimized with multi-stage builds

3. **Reduce Image Size**:
   - Only production dependencies are installed (`--no-dev`)
   - Multi-stage build removes build tools
   - `.dockerignore` excludes unnecessary files

## Security Notes

- Container runs as non-root user (UID 1000)
- No secrets in the image (use environment variables)
- Regular security updates via base image updates
- Health checks enabled for monitoring

## Next Steps

Once local testing is successful:
1. Push to Digital Ocean registry
2. Update `k8s/deployment.yaml` with your image name
3. Follow the [Kubernetes Deployment Guide](k8s/README.md)
4. Or let GitHub Actions handle the deployment automatically

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Digital Ocean Container Registry](https://docs.digitalocean.com/products/container-registry/)
- [doctl CLI Reference](https://docs.digitalocean.com/reference/doctl/)
