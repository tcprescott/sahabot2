# Swagger/OpenAPI Documentation Guide

## Accessing API Documentation

The SahaBot2 API includes interactive documentation powered by Swagger UI and ReDoc.

### Development Mode

When `DEBUG=True` in your `.env` file:

- **Swagger UI**: http://localhost:8080/docs
  - Interactive interface
  - Test endpoints directly in the browser
  - Built-in authentication support
  
- **ReDoc**: http://localhost:8080/redoc
  - Clean, responsive documentation
  - Detailed schemas and examples
  - Print-friendly format

### Production Mode

When `DEBUG=False` (production):
- API documentation is **disabled** for security
- Only the API endpoints themselves remain accessible

## Using Swagger UI

### 1. Authentication

Click the **"Authorize"** button (lock icon) in the top right:
1. Enter your Bearer token in the format: `YOUR_TOKEN_HERE` (without "Bearer" prefix)
2. Click "Authorize"
3. Click "Close"

All subsequent requests will include your token automatically.

### 2. Testing Endpoints

For each endpoint, you can:
1. Click to expand the endpoint details
2. Click **"Try it out"**
3. Fill in any required parameters
4. Click **"Execute"**
5. View the response below (status code, headers, body)

### 3. Viewing Schemas

Scroll to the bottom of the Swagger UI page to see:
- **Schemas**: All request/response data models
- **Field descriptions**: What each field represents
- **Examples**: Sample data for each schema

## API Features Documented

### Endpoints

✅ **Health Check** (`/api/health`)
- No authentication required
- Returns service status and version
- Useful for monitoring and health checks

✅ **User Endpoints** (`/api/users/*`)
- All require Bearer token authentication
- Permission-based access control
- Rate limited per user

### Response Documentation

Each endpoint includes:
- **Summary**: Brief description
- **Description**: Detailed explanation
- **Parameters**: Query/path/body parameters with validation rules
- **Responses**: All possible status codes (200, 401, 403, 429, etc.)
- **Examples**: Sample responses
- **Security**: Required authentication

### Schema Documentation

All schemas include:
- **Field types**: Data type for each field
- **Descriptions**: What each field represents
- **Validation**: Min/max length, required fields, etc.
- **Examples**: Sample values

## Rate Limiting

Rate limit information is documented:
- Default limits shown in API description
- 429 responses documented for all endpoints
- `Retry-After` header explained

## Permission Levels

Permission requirements are clearly indicated:
- USER (0) - Basic authenticated access
- MODERATOR (50) - Moderation actions
- ADMIN (100) - Administrative access
- SUPERADMIN (200) - Full access

Each endpoint shows which permission level is required.

## Tips

1. **Use "Try it out"** to test endpoints without writing code
2. **Check the Schemas section** to understand response structures
3. **Look at Examples** to see what data looks like
4. **Review error responses** (401, 403, 429) to handle them in your code
5. **Export the OpenAPI spec** (available at `/openapi.json`) for code generation tools

## Common Use Cases

### Generate API Token
Currently via service layer (UI coming soon):
```python
from application.services.api_token_service import ApiTokenService
service = ApiTokenService()
token, api_token = await service.generate_token(user)
print(f"Your token: {token}")
```

### Test Authentication
1. Get a token (see above)
2. Go to http://localhost:8080/docs
3. Click "Authorize"
4. Paste your token
5. Try the `/api/users/me` endpoint

### Check Rate Limits
Make repeated requests to any endpoint and observe:
- First 60 requests succeed (200 OK)
- 61st request returns 429 Too Many Requests
- `Retry-After` header tells you when to retry

## Troubleshooting

### "Docs not found" error
- Make sure `DEBUG=True` in your `.env` file
- Restart the application after changing `.env`

### "401 Unauthorized" on all requests
- Click "Authorize" and add your Bearer token
- Make sure token is valid (check database or regenerate)

### "403 Forbidden" on some endpoints
- Your token's user needs higher permissions
- Check endpoint docs for required permission level
- Update user permission in database if needed

## Next Steps

Once API tokens can be managed via UI:
- Users can generate their own tokens
- Tokens can be revoked/regenerated
- Per-user rate limits can be customized

For now, tokens must be generated programmatically via the service layer.
