# Health Check Endpoint

The health check endpoint provides a way to monitor the status of the SahaBot2 application and its upstream services.

## Endpoint

```
GET /api/health?secret={HEALTH_CHECK_SECRET}
```

## Authentication

The endpoint requires a `secret` query parameter that matches the `HEALTH_CHECK_SECRET` environment variable.

### Configuration

Add to your `.env` file:

```env
HEALTH_CHECK_SECRET=your_secure_secret_here
```

**Security Note**: Use a strong, randomly generated secret in production. This secret should be treated as sensitive and not committed to version control.

## Response Format

### Success Response (200 OK)

When all services are healthy:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "services": {
    "database": {
      "status": "ok",
      "message": "Database connection healthy"
    }
  }
}
```

### Degraded Response (200 OK)

When one or more services are unhealthy but the API is still operational:

```json
{
  "status": "degraded",
  "version": "0.1.0",
  "services": {
    "database": {
      "status": "error",
      "message": "Database connection failed: Connection refused"
    }
  }
}
```

### Error Responses

#### 401 Unauthorized
Invalid or missing secret:

```json
{
  "detail": "Invalid health check secret"
}
```

#### 422 Unprocessable Entity
Missing required query parameter:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "secret"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

## Usage Examples

### Using curl

```bash
# Check health with valid secret
curl "http://localhost:8080/api/health?secret=your_secret_here"

# Response when healthy
# {"status":"ok","version":"0.1.0","services":{"database":{"status":"ok","message":"Database connection healthy"}}}
```

### Using Python requests

```python
import requests

secret = "your_secret_here"
response = requests.get(f"http://localhost:8080/api/health?secret={secret}")

if response.status_code == 200:
    data = response.json()
    if data["status"] == "ok":
        print("Service is healthy")
    elif data["status"] == "degraded":
        print("Service is degraded")
        for service, status in data["services"].items():
            if status["status"] == "error":
                print(f"  {service}: {status['message']}")
else:
    print(f"Health check failed: {response.status_code}")
```

## Monitoring Integration

### Kubernetes Liveness/Readiness Probes

```yaml
livenessProbe:
  httpGet:
    path: /api/health?secret=${HEALTH_CHECK_SECRET}
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /api/health?secret=${HEALTH_CHECK_SECRET}
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 2
```

### Uptime Monitoring Services

Configure your monitoring service (e.g., UptimeRobot, Pingdom) to:
1. Make a GET request to `/api/health?secret={your_secret}`
2. Expect HTTP 200 status code
3. Optionally check response body for `"status":"ok"`

### Load Balancer Health Checks

Configure your load balancer (e.g., AWS ELB, nginx) to:
- **Protocol**: HTTP
- **Path**: `/api/health?secret={your_secret}`
- **Expected Status**: 200
- **Interval**: 30 seconds
- **Timeout**: 5 seconds
- **Healthy threshold**: 2
- **Unhealthy threshold**: 3

## Monitored Services

The health check currently monitors:

### Database
- **Check**: Executes a simple query (`SELECT 1`) to verify database connectivity
- **Status**: `ok` if query succeeds, `error` if query fails
- **Message**: Describes the current state or error details

## Implementation Details

The health check endpoint:
1. Validates the provided secret against `HEALTH_CHECK_SECRET`
2. Performs connectivity checks on all upstream services
3. Returns overall status based on service health:
   - `ok`: All services are healthy
   - `degraded`: One or more services are unhealthy
   - `error`: Critical failure (not currently used)

For more details, see the implementation in [`api/routes/health.py`](../api/routes/health.py).
