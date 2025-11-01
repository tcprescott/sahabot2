# Deployment Checklist

Use this checklist to ensure a smooth deployment to Digital Ocean Kubernetes.

## Pre-Deployment

### 1. Digital Ocean Setup
- [ ] Create Digital Ocean account
- [ ] Create Managed Kubernetes cluster
  - [ ] Choose appropriate cluster size (recommended: 2+ nodes)
  - [ ] Note cluster ID/name
- [ ] Create Container Registry
  - [ ] Note registry name
- [ ] Generate API token with read/write access
  - [ ] Save token securely

### 2. GitHub Configuration
- [ ] Add GitHub secrets to repository:
  - [ ] `DIGITALOCEAN_ACCESS_TOKEN`
  - [ ] `DIGITALOCEAN_REGISTRY_NAME`
  - [ ] `DIGITALOCEAN_CLUSTER_ID`
- [ ] Verify secrets are added (Settings → Secrets and variables → Actions)

### 3. Application Configuration
- [ ] Update `k8s/secrets.yaml`:
  - [ ] Database credentials (if using external DB)
  - [ ] Discord OAuth2 credentials
  - [ ] Discord bot token
  - [ ] Secret key (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
  - [ ] Base URL (your domain)
  - [ ] Redirect URI (your domain + /auth/callback)
- [ ] Update `k8s/deployment.yaml`:
  - [ ] Replace `YOUR_REGISTRY_NAME` with actual registry name
- [ ] Run validation: `python3 tools/validate_k8s.py`
  - [ ] Fix any warnings or errors

### 4. Database Setup (Choose One)

#### Option A: In-Cluster MySQL
- [ ] Review `k8s/mysql.yaml` configuration
- [ ] Adjust storage size if needed (default: 10Gi)
- [ ] Ready to deploy with other manifests

#### Option B: External Database
- [ ] Provision MySQL database (DO Managed Database recommended)
- [ ] Create database and user
- [ ] Update `DB_HOST` in `k8s/secrets.yaml` with external host
- [ ] Ensure firewall allows connections from Kubernetes cluster
- [ ] Test connection from local machine

## Initial Deployment

### Manual Deployment (Recommended for First Time)

1. **Install Required Tools**
   - [ ] Install `kubectl`
   - [ ] Install `doctl`
   - [ ] Install Docker (for local testing)

2. **Authenticate with Digital Ocean**
   ```bash
   doctl auth init
   doctl kubernetes cluster kubeconfig save <cluster-name>
   ```
   - [ ] Verify connection: `kubectl cluster-info`

3. **Build and Push Container**
   ```bash
   docker build -t registry.digitalocean.com/<registry>/sahabot2:latest .
   doctl registry login
   docker push registry.digitalocean.com/<registry>/sahabot2:latest
   ```
   - [ ] Verify image in registry: `doctl registry repository list-tags sahabot2`

4. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/secrets.yaml
   kubectl apply -f k8s/mysql.yaml  # If using in-cluster MySQL
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```
   - [ ] Wait for pods to be ready: `kubectl get pods -n sahabot2 -w`

5. **Run Database Migrations**
   ```bash
   POD_NAME=$(kubectl get pods -n sahabot2 -l app=sahabot2 -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n sahabot2 $POD_NAME -- poetry run aerich init-db
   ```
   - [ ] Verify migrations completed successfully

6. **Verify Deployment**
   - [ ] Check pods: `kubectl get pods -n sahabot2`
   - [ ] Check service: `kubectl get svc -n sahabot2`
   - [ ] Get LoadBalancer IP
   - [ ] Test health endpoint: `curl http://<LB-IP>/api/health`

### Automated Deployment (After Initial Setup)

1. **Trigger Deployment**
   - [ ] Push to `main` branch, OR
   - [ ] Create version tag: `git tag v1.0.0 && git push origin v1.0.0`, OR
   - [ ] Manually trigger via GitHub Actions UI

2. **Monitor Deployment**
   - [ ] Watch GitHub Actions workflow
   - [ ] Monitor pod status: `kubectl get pods -n sahabot2 -w`
   - [ ] Check logs: `kubectl logs -n sahabot2 -l app=sahabot2 -f`

## Post-Deployment

### 1. DNS Configuration
- [ ] Create DNS A record pointing to LoadBalancer IP
- [ ] Wait for DNS propagation (can take up to 48 hours)
- [ ] Verify: `dig your-domain.com`

### 2. SSL/TLS Setup (Optional but Recommended)
- [ ] Install cert-manager
- [ ] Create Ingress resource with TLS
- [ ] Configure Let's Encrypt issuer
- [ ] Update Discord OAuth2 redirect URI to HTTPS

### 3. Monitoring Setup
- [ ] Check pod logs: `kubectl logs -n sahabot2 -l app=sahabot2`
- [ ] Monitor resource usage: `kubectl top pods -n sahabot2`
- [ ] Set up alerts (optional, via DO monitoring)
- [ ] Test application functionality:
  - [ ] Access web interface
  - [ ] Test Discord OAuth login
  - [ ] Test Discord bot commands
  - [ ] Verify database connectivity

### 4. Security Hardening
- [ ] Review secrets - ensure no default/placeholder values
- [ ] Rotate API tokens quarterly
- [ ] Enable network policies (optional)
- [ ] Review pod security policies
- [ ] Set up backup for database
- [ ] Document emergency procedures

### 5. Performance Tuning
- [ ] Monitor application performance
- [ ] Adjust replica count if needed
- [ ] Adjust resource limits based on actual usage
- [ ] Configure Horizontal Pod Autoscaler (optional)

## Troubleshooting Reference

### Common Issues

**Pods not starting:**
- [ ] Check logs: `kubectl logs -n sahabot2 <pod-name>`
- [ ] Describe pod: `kubectl describe pod -n sahabot2 <pod-name>`
- [ ] Verify secrets: `kubectl get secret -n sahabot2`

**ImagePullBackOff:**
- [ ] Verify registry credentials
- [ ] Check image name/tag is correct
- [ ] Ensure image was pushed successfully

**Database connection failures:**
- [ ] Verify database is running
- [ ] Check connection string in secrets
- [ ] Test connectivity from pod: `kubectl exec -n sahabot2 <pod> -- ping <db-host>`

**Service not accessible:**
- [ ] Check LoadBalancer status: `kubectl get svc -n sahabot2`
- [ ] Verify firewall rules
- [ ] Check service endpoints: `kubectl get endpoints -n sahabot2`

## Rollback Procedure

If deployment fails or issues are discovered:

1. **Via kubectl:**
   ```bash
   kubectl rollout undo deployment/sahabot2 -n sahabot2
   kubectl rollout status deployment/sahabot2 -n sahabot2
   ```

2. **Via GitHub Actions:**
   - Trigger deploy workflow
   - Specify previous working image tag

3. **Verify:**
   - [ ] Check pods are running
   - [ ] Test application functionality
   - [ ] Monitor logs for errors

## Maintenance Schedule

### Weekly
- [ ] Review application logs
- [ ] Check resource usage
- [ ] Monitor costs in DO dashboard

### Monthly
- [ ] Update dependencies: `poetry update`
- [ ] Rebuild and deploy container
- [ ] Review security advisories

### Quarterly
- [ ] Rotate API tokens and secrets
- [ ] Review and update resource limits
- [ ] Backup and test restore procedures
- [ ] Review and update documentation

## Documentation References

- [Kubernetes Deployment Guide](k8s/README.md)
- [Docker Quick Start](docs/DOCKER.md)
- [CI/CD Pipeline](docs/CICD.md)
- [Digital Ocean Kubernetes Docs](https://docs.digitalocean.com/products/kubernetes/)

## Emergency Contacts

- Repository Issues: [GitHub Issues](https://github.com/tcprescott/sahabot2/issues)
- Digital Ocean Support: https://www.digitalocean.com/support
- Discord Developer Portal: https://discord.com/developers

---

**Note:** This checklist is designed for the initial deployment. After the first successful deployment, most tasks are automated via GitHub Actions.
