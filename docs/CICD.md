# CI/CD Pipeline Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for SahaBot2.

## Overview

The CI/CD pipeline consists of three main workflows:

1. **Configuration Policy Checks** - Validates code follows configuration best practices
2. **Build and Push Container** - Builds Docker image and pushes to Digital Ocean Container Registry
3. **Deploy to Kubernetes** - Deploys the application to Digital Ocean Kubernetes

## Workflows

### 1. Configuration Policy Checks

**File**: `.github/workflows/config-policy.yml`

**Trigger**: 
- Push to `main` branch
- Pull requests to `main` branch

**Purpose**: Ensures all configuration is loaded from `config.py` and not accessed directly from environment variables.

**Steps**:
1. Checkout repository
2. Set up Python 3.11
3. Run `tools/check_config_policy.py`

**Success Criteria**: All Python files must use `from config import settings` instead of `os.getenv()` or `os.environ`.

### 2. Build and Push Container

**File**: `.github/workflows/build-container.yml`

**Trigger**:
- Push to `main` branch
- Push of version tags (e.g., `v1.0.0`)
- Pull requests to `main` branch (build only, no push)

**Purpose**: Builds the Docker container and pushes to Digital Ocean Container Registry.

**Steps**:
1. Checkout repository
2. Set up Docker Buildx for advanced build features
3. Login to Digital Ocean Container Registry (skip for PRs)
4. Extract metadata for Docker tags and labels
5. Build and push Docker image with caching
6. Output image digest

**Image Tags Generated**:
- `latest` - For pushes to main branch
- `main-<git-sha>` - For pushes to main branch
- `v1.0.0`, `v1.0`, `v1` - For version tags
- `pr-<number>` - For pull requests

**Required Secrets**:
- `DIGITALOCEAN_ACCESS_TOKEN` - Digital Ocean API token
- `DIGITALOCEAN_REGISTRY_NAME` - Registry name (e.g., `my-registry`)

**Cache Strategy**: GitHub Actions cache is used to speed up builds.

### 3. Deploy to Kubernetes

**File**: `.github/workflows/deploy-k8s.yml`

**Trigger**:
- Automatically after successful "Build and Push Container" workflow on `main` branch
- Manual trigger via GitHub Actions UI (workflow_dispatch)

**Purpose**: Deploys the application to Digital Ocean Kubernetes cluster.

**Steps**:
1. Checkout repository
2. Install and configure `doctl` (Digital Ocean CLI)
3. Save Kubernetes cluster credentials
4. Determine image tag to deploy (latest or specified)
5. Update deployment with new image
6. Wait for rollout to complete (timeout: 5 minutes)
7. Verify deployment
8. Run database migrations
9. Display deployment information

**Required Secrets**:
- `DIGITALOCEAN_ACCESS_TOKEN` - Digital Ocean API token
- `DIGITALOCEAN_REGISTRY_NAME` - Registry name
- `DIGITALOCEAN_CLUSTER_ID` - Kubernetes cluster ID or name

**Manual Deployment**:
You can manually trigger deployment with a specific image tag:
1. Go to Actions → Deploy to Kubernetes
2. Click "Run workflow"
3. Select branch
4. Enter image tag (default: `latest`)
5. Click "Run workflow"

## GitHub Secrets Setup

### Required Secrets

Navigate to repository Settings → Secrets and variables → Actions, then add:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `DIGITALOCEAN_ACCESS_TOKEN` | Digital Ocean API token with read/write access | `dop_v1_1234567890abcdef...` |
| `DIGITALOCEAN_REGISTRY_NAME` | Your container registry name | `my-company-registry` |
| `DIGITALOCEAN_CLUSTER_ID` | Kubernetes cluster ID or name | `k8s-sahabot-prod` |

### Creating Digital Ocean API Token

1. Log in to Digital Ocean
2. Go to API → Tokens/Keys
3. Click "Generate New Token"
4. Name: `GitHub Actions - SahaBot2`
5. Scopes: Select "Read" and "Write"
6. Click "Generate Token"
7. Copy the token immediately (shown only once)

### Getting Registry Name

```bash
# Using doctl
doctl registry get --format Name --no-header

# Or find in DO dashboard: Container Registry → Your Registry Name
```

### Getting Cluster ID

```bash
# Using doctl
doctl kubernetes cluster list --format ID,Name --no-header

# Or find in DO dashboard: Kubernetes → Your Cluster → Settings
```

## Deployment Flow

### Automatic Deployment (Main Branch)

```
┌─────────────────┐
│  Push to main   │
└────────┬────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│ Config Policy    │            │ Build Container  │
│ Checks           │            │                  │
└────────┬─────────┘            └────────┬─────────┘
         │                               │
         │ (independent)                 │
         │                               ▼
         │                      ┌──────────────────┐
         │                      │ Push to Registry │
         │                      └────────┬─────────┘
         │                               │
         │                               ▼
         │                      ┌──────────────────┐
         │                      │ Deploy to K8s    │
         │                      │ - Update image   │
         │                      │ - Run migrations │
         │                      │ - Verify deploy  │
         │                      └──────────────────┘
         │
         ▼
     Success
```

### Version Release Deployment

```
┌─────────────────┐
│ Push version    │
│ tag (v1.0.0)    │
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ Build Container  │
│ with version tag │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Push to Registry │
│ - v1.0.0         │
│ - v1.0           │
│ - v1             │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Manual Deploy    │
│ (if desired)     │
└──────────────────┘
```

## Environment-Specific Deployments

Currently, the pipeline deploys to a single production environment. To add staging:

### Option 1: Separate Clusters

```yaml
# .github/workflows/deploy-staging.yml
on:
  push:
    branches: [ develop ]

env:
  CLUSTER_ID: ${{ secrets.STAGING_CLUSTER_ID }}
```

### Option 2: Namespaces in Same Cluster

Update `deploy-k8s.yml` to use different namespaces:

```yaml
- name: Set namespace
  run: |
    if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
      echo "NAMESPACE=sahabot2-prod" >> $GITHUB_ENV
    else
      echo "NAMESPACE=sahabot2-staging" >> $GITHUB_ENV
    fi
```

## Rollback Procedures

### Automated Rollback

If deployment fails, Kubernetes automatically rolls back to the previous version.

### Manual Rollback

#### Via GitHub Actions

1. Go to Actions → Deploy to Kubernetes
2. Click "Run workflow"
3. Enter the previous image tag (e.g., `v1.0.0`)
4. Click "Run workflow"

#### Via kubectl

```bash
# View rollout history
kubectl rollout history deployment/sahabot2 -n sahabot2

# Rollback to previous version
kubectl rollout undo deployment/sahabot2 -n sahabot2

# Rollback to specific revision
kubectl rollout undo deployment/sahabot2 --to-revision=3 -n sahabot2
```

## Monitoring Deployments

### GitHub Actions UI

1. Go to repository → Actions
2. Click on workflow run
3. View logs for each step
4. Check deployment status

### Command Line

```bash
# Watch deployment status
kubectl rollout status deployment/sahabot2 -n sahabot2 -w

# Get recent events
kubectl get events -n sahabot2 --sort-by='.lastTimestamp'

# Check pods
kubectl get pods -n sahabot2 -w
```

## Troubleshooting

### Build Fails

**Error: "Poetry lock file is inconsistent"**
- Run `poetry lock --no-update` locally and commit

**Error: "Could not find a version that satisfies requirement"**
- Update `pyproject.toml` or `poetry.lock`
- Ensure Python version matches Dockerfile

### Push Fails

**Error: "unauthorized: authentication required"**
- Check `DIGITALOCEAN_ACCESS_TOKEN` secret is valid
- Ensure token has write access to registry

**Error: "denied: repository does not exist"**
- Create registry in Digital Ocean dashboard
- Update `DIGITALOCEAN_REGISTRY_NAME` secret

### Deploy Fails

**Error: "cluster not found"**
- Verify `DIGITALOCEAN_CLUSTER_ID` secret
- Ensure cluster exists and is running

**Error: "ImagePullBackOff"**
- Check image was pushed successfully
- Verify registry credentials in cluster:
  ```bash
  kubectl get secret digitalocean-registry -n sahabot2
  ```

**Error: "CrashLoopBackOff"**
- Check pod logs: `kubectl logs -n sahabot2 <pod-name>`
- Verify secrets are configured correctly
- Check database connectivity

### Migration Fails

**Error: "migration already applied"**
- This is usually safe to ignore
- Or remove the migration check from workflow

**Error: "database connection failed"**
- Verify database is running
- Check database credentials in secrets

## Best Practices

1. **Always test builds locally** before pushing to main
2. **Use pull requests** for code review before deployment
3. **Tag releases** with semantic versioning (v1.0.0)
4. **Monitor logs** after deployment
5. **Test in staging** before production (if available)
6. **Keep secrets secure** - never commit to repository
7. **Document changes** in commit messages
8. **Run validation script** before deploying: `python3 tools/validate_k8s.py`

## Security Considerations

- API tokens are stored as GitHub encrypted secrets
- Secrets are never logged in workflow output
- Container runs as non-root user
- Multi-stage build minimizes attack surface
- Dependencies are pinned in `poetry.lock`
- Regular base image updates for security patches

## Performance Optimization

- **Build cache**: Docker layer caching speeds up builds
- **Multi-stage builds**: Reduces final image size
- **Parallel jobs**: Policy checks run independently
- **Strategic triggers**: PRs build but don't deploy

## Maintenance

### Regular Updates

- Update base image monthly: `python:3.13-slim`
- Update dependencies: `poetry update`
- Update GitHub Actions versions
- Rotate API tokens quarterly

### Monitoring Costs

Digital Ocean charges for:
- Container registry storage
- Bandwidth for pulling images
- Kubernetes cluster resources

Monitor in DO dashboard → Billing.

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Digital Ocean Container Registry](https://docs.digitalocean.com/products/container-registry/)
- [Digital Ocean Kubernetes](https://docs.digitalocean.com/products/kubernetes/)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [doctl Reference](https://docs.digitalocean.com/reference/doctl/)
