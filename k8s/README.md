# Kubernetes Deployment Guide

This guide explains how to deploy SahaBot2 to Digital Ocean's Managed Kubernetes service using the provided manifests and GitHub Actions workflows.

## Prerequisites

1. **Digital Ocean Account** with:
   - A Managed Kubernetes cluster created
   - A Container Registry created
   - An API token with read/write access

2. **Required Tools** (for manual deployment):
   - `kubectl` - Kubernetes CLI
   - `doctl` - Digital Ocean CLI
   - Docker (for local testing)

3. **GitHub Secrets** (for automated deployment):
   - `DIGITALOCEAN_ACCESS_TOKEN` - Your DO API token
   - `DIGITALOCEAN_REGISTRY_NAME` - Your DO registry name (e.g., `my-registry`)
   - `DIGITALOCEAN_CLUSTER_ID` - Your Kubernetes cluster ID or name

## Validation

Before deploying, validate your configuration:

```bash
python3 tools/validate_k8s.py
```

This script checks:
- YAML syntax of all manifests
- Whether secrets have been customized from template values
- Whether deployment image registry is configured
- GitHub Actions workflow syntax

## Architecture Overview

The deployment consists of:
- **Namespace**: `sahabot2` - Isolated namespace for the application
- **Deployment**: 2 replicas with rolling update strategy
- **Service**: LoadBalancer service exposing the application on port 80
- **Secrets**: Configuration and credentials stored as Kubernetes secrets
- **MySQL** (optional): StatefulSet with persistent storage

## Automated Deployment with GitHub Actions

### Setup

1. **Add GitHub Secrets**:
   - Go to your repository Settings → Secrets and variables → Actions
   - Add the following secrets:
     ```
     DIGITALOCEAN_ACCESS_TOKEN=<your-do-api-token>
     DIGITALOCEAN_REGISTRY_NAME=<your-registry-name>
     DIGITALOCEAN_CLUSTER_ID=<your-cluster-name-or-id>
     ```

2. **Update Configuration**:
   - Edit `k8s/secrets.yaml` with your actual configuration values
   - Edit `k8s/deployment.yaml` to reference your registry:
     ```yaml
     image: registry.digitalocean.com/YOUR_REGISTRY_NAME/sahabot2:latest
     ```

3. **Initial Kubernetes Setup** (one-time):
   ```bash
   # Install doctl and authenticate
   doctl auth init

   # Connect to your cluster
   doctl kubernetes cluster kubeconfig save <cluster-name>

   # Apply Kubernetes manifests
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/secrets.yaml
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   
   # Optional: Deploy MySQL in Kubernetes
   kubectl apply -f k8s/mysql.yaml
   ```

### Workflow Triggers

**Build and Push Container** (`.github/workflows/build-container.yml`):
- Triggered on push to `main` branch
- Triggered on version tags (e.g., `v1.0.0`)
- Triggered on pull requests (build only, no push)

**Deploy to Kubernetes** (`.github/workflows/deploy-k8s.yml`):
- Automatically triggered after successful container build
- Can be manually triggered via GitHub Actions UI
- Performs rolling update to new container image
- Runs database migrations automatically

### Manual Deployment Trigger

You can manually trigger a deployment:

1. Go to Actions → Deploy to Kubernetes → Run workflow
2. Select the branch
3. Optionally specify an image tag (default: `latest`)
4. Click "Run workflow"

## Manual Deployment

### 1. Build and Push Container

```bash
# Build the container
docker build -t sahabot2:latest .

# Tag for Digital Ocean registry
docker tag sahabot2:latest registry.digitalocean.com/<registry-name>/sahabot2:latest

# Login to DO registry
doctl registry login

# Push the image
docker push registry.digitalocean.com/<registry-name>/sahabot2:latest
```

### 2. Configure Kubernetes

```bash
# Connect to your cluster
doctl kubernetes cluster kubeconfig save <cluster-name>

# Verify connection
kubectl cluster-info
```

### 3. Update Secrets

Edit `k8s/secrets.yaml` with your actual configuration:

```yaml
stringData:
  DB_HOST: "mysql-service.sahabot2.svc.cluster.local"  # or external DB host
  DB_PASSWORD: "your-secure-password"
  DISCORD_CLIENT_ID: "your-discord-client-id"
  DISCORD_CLIENT_SECRET: "your-discord-client-secret"
  DISCORD_BOT_TOKEN: "your-bot-token"
  SECRET_KEY: "your-long-random-secret-key"
  BASE_URL: "https://your-domain.com"
  DISCORD_REDIRECT_URI: "https://your-domain.com/auth/callback"
```

**Important**: For production, consider using a secrets management solution like:
- External Secrets Operator with Digital Ocean Secrets Manager
- Sealed Secrets
- Vault

### 4. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets
kubectl apply -f k8s/secrets.yaml

# Deploy MySQL (optional - or use external database)
kubectl apply -f k8s/mysql.yaml

# Wait for MySQL to be ready
kubectl wait --for=condition=ready pod -l app=mysql -n sahabot2 --timeout=300s

# Deploy the application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Wait for deployment to be ready
kubectl wait --for=condition=available deployment/sahabot2 -n sahabot2 --timeout=300s
```

### 5. Run Database Migrations

```bash
# Get a pod name
POD_NAME=$(kubectl get pods -n sahabot2 -l app=sahabot2 -o jsonpath='{.items[0].metadata.name}')

# Initialize database (first time only)
kubectl exec -n sahabot2 $POD_NAME -- poetry run aerich init-db

# Or apply migrations (subsequent deployments)
kubectl exec -n sahabot2 $POD_NAME -- poetry run aerich upgrade
```

### 6. Verify Deployment

```bash
# Check deployment status
kubectl get deployments -n sahabot2

# Check pods
kubectl get pods -n sahabot2

# Check service and get LoadBalancer IP
kubectl get service sahabot2-service -n sahabot2

# View logs
kubectl logs -n sahabot2 -l app=sahabot2 --tail=100 -f
```

## Configuration

### Environment Variables

All configuration is managed through the `sahabot2-secrets` secret. Update it with:

```bash
kubectl edit secret sahabot2-secrets -n sahabot2
```

Or update the file and reapply:

```bash
kubectl apply -f k8s/secrets.yaml
kubectl rollout restart deployment/sahabot2 -n sahabot2
```

### Scaling

Scale the deployment:

```bash
# Scale up
kubectl scale deployment sahabot2 --replicas=3 -n sahabot2

# Or edit the deployment
kubectl edit deployment sahabot2 -n sahabot2
```

### Resource Limits

Default resource limits are set in `k8s/deployment.yaml`:
- Requests: 512Mi memory, 250m CPU
- Limits: 1Gi memory, 500m CPU

Adjust based on your workload:

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

## Monitoring and Troubleshooting

### View Logs

```bash
# All pods
kubectl logs -n sahabot2 -l app=sahabot2 --tail=100

# Specific pod
kubectl logs -n sahabot2 <pod-name> -f

# Previous instance (if crashed)
kubectl logs -n sahabot2 <pod-name> --previous
```

### Check Pod Status

```bash
# Get pods
kubectl get pods -n sahabot2

# Describe pod for events
kubectl describe pod <pod-name> -n sahabot2

# Get pod metrics
kubectl top pods -n sahabot2
```

### Health Checks

The deployment includes:
- **Liveness Probe**: Checks `/api/health` every 10s
- **Readiness Probe**: Checks `/api/health` every 5s

Test health endpoint:

```bash
# Port forward to test locally
kubectl port-forward -n sahabot2 service/sahabot2-service 8080:80

# Test in browser
curl http://localhost:8080/api/health
```

### Common Issues

**Pods not starting:**
- Check logs: `kubectl logs -n sahabot2 <pod-name>`
- Check events: `kubectl describe pod <pod-name> -n sahabot2`
- Verify secrets are configured correctly

**Database connection issues:**
- Verify MySQL is running: `kubectl get pods -n sahabot2 -l app=mysql`
- Check DB credentials in secrets
- Verify DB_HOST is correct (for external DB, use full hostname)

**Image pull errors:**
- Verify registry credentials: `kubectl get secret digitalocean-registry -n sahabot2`
- Create registry secret if missing:
  ```bash
  doctl registry kubernetes-manifest | kubectl apply -f -
  ```

## Updates and Rollbacks

### Update to New Version

```bash
# Tag and push new image
docker build -t sahabot2:v1.0.1 .
docker tag sahabot2:v1.0.1 registry.digitalocean.com/<registry>/sahabot2:v1.0.1
docker push registry.digitalocean.com/<registry>/sahabot2:v1.0.1

# Update deployment
kubectl set image deployment/sahabot2 sahabot2=registry.digitalocean.com/<registry>/sahabot2:v1.0.1 -n sahabot2

# Watch rollout
kubectl rollout status deployment/sahabot2 -n sahabot2
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/sahabot2 -n sahabot2

# Rollback to specific revision
kubectl rollout history deployment/sahabot2 -n sahabot2
kubectl rollout undo deployment/sahabot2 --to-revision=2 -n sahabot2
```

## External Database

To use an external MySQL database instead of the in-cluster one:

1. Skip applying `k8s/mysql.yaml`
2. Update `k8s/secrets.yaml`:
   ```yaml
   DB_HOST: "your-external-db-host"
   DB_PORT: "3306"
   DB_USER: "your-db-user"
   DB_PASSWORD: "your-db-password"
   DB_NAME: "sahabot2"
   ```
3. Ensure the external database allows connections from your cluster IPs

## Security Best Practices

1. **Use Sealed Secrets or External Secrets Operator** for production secrets management
2. **Enable Network Policies** to restrict pod-to-pod communication
3. **Use RBAC** to limit access to namespaces and resources
4. **Enable Pod Security Policies** or Pod Security Standards
5. **Regularly update** container images for security patches
6. **Use private registry** and scan images for vulnerabilities
7. **Enable audit logging** in Kubernetes
8. **Rotate credentials** regularly

## Custom Domain and SSL

To use a custom domain with SSL:

1. **Point DNS** to LoadBalancer IP:
   ```bash
   kubectl get service sahabot2-service -n sahabot2 -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
   ```

2. **Install cert-manager** for automatic SSL:
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   ```

3. **Create Ingress** with TLS (example in `k8s/ingress.yaml` - not included, customize as needed)

## Cost Optimization

- Use **Horizontal Pod Autoscaler** to scale based on load
- Set appropriate **resource requests/limits** to avoid over-provisioning
- Consider using **Spot/Preemptible nodes** for non-production
- Use **Digital Ocean Spaces** for static assets instead of local storage
- Monitor costs in Digital Ocean dashboard

## Support

For issues specific to:
- **Kubernetes manifests**: Check this repository's issues
- **Digital Ocean**: Consult [DO Kubernetes documentation](https://docs.digitalocean.com/products/kubernetes/)
- **Application errors**: Check application logs and GitHub issues

## References

- [Digital Ocean Kubernetes Documentation](https://docs.digitalocean.com/products/kubernetes/)
- [Digital Ocean Container Registry](https://docs.digitalocean.com/products/container-registry/)
- [doctl CLI Reference](https://docs.digitalocean.com/reference/doctl/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
