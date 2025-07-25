# OAuth Tool Plugin Development Guide for Dify

OAuth (Open Authorization) is a better way to authorize tool plugins that need to access user data from third-party services like Gmail or GitHub. Instead of requiring the user to manually enter API keys, OAuth provides a secure way to act on behalf of the user with their explicit consent.

## Overview of the OAuth Flow

1. **User initiates**: User adds your tool and clicks "Connect" 
2. **Authorization**: User is redirected to the service (e.g., Google) to grant permissions
3. **Callback**: Service redirects back to Dify with an authorization code
4. **Token exchange**: Your plugin exchanges the code for access tokens
5. **API access**: Your plugin uses tokens to make API calls on user's behalf

## Setting Up Third-Party Services

You usually need to register an OAuth app at the third-party service so the service knows who is requesting the permissions. Here we use Gmail as an example. Other platforms may be different.

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing one
   - Enable the required APIs (e.g., Gmail API, Google Drive API)

2. **Configure OAuth Consent Screen**:
   - Navigate to "APIs & Services" → "OAuth consent screen"
   - Choose "External" user type for public plugins
   - Fill in application name, user support email, and developer contact
   - Add authorized domains if needed
   - For testing: Add test users in the "Test users" section

3. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Choose "Web application" type
   - Add authorized redirect URIs:
     ```
     https://cloud.dify.ai/console/api/oauth/plugin/{plugin-id}/{provider-name}/{tool-name}/callback
     ```
   - Save the Client ID and Client Secret

## Implementation Guide

### 1. Required OAuth Methods in Tool Provider

Your `ToolProvider` class must implement these four OAuth methods:

#### `_oauth_get_authorization_url()`
**Purpose**: Generate the OAuth authorization URL where users will grant permissions
**Input**: 
- `redirect_uri: str` - Dify-provided callback URL
- `system_credentials: Mapping[str, Any]` - Contains `client_id`, `client_secret` from provider config
**Output**: `str` - Complete authorization URL
**Key Tasks**:
- Build OAuth URL with client_id, redirect_uri, scopes, and state parameter
- Include `access_type=offline` and `prompt=consent` for refresh tokens

#### `_oauth_get_credentials()`
**Purpose**: Exchange authorization code for access tokens
**Input**:
- `redirect_uri: str` - Same redirect URI used in authorization
- `system_credentials: Mapping[str, Any]` - Client credentials
- `request: Request` - Contains authorization code in `request.args.get("code")`
**Output**: `ToolOAuthCredentials` - Wrapped credentials with expiration
**Key Tasks**:
- Extract authorization code from request
- POST to token endpoint with code, client credentials, and grant_type
- Wrap response in `ToolOAuthCredentials(credentials=creds_dict, expires_at=timestamp)`

#### `_oauth_refresh_credentials()`
**Purpose**: Refresh expired access tokens using refresh token
**Input**:
- `redirect_uri: str` - Original redirect URI
- `system_credentials: Mapping[str, Any]` - Client credentials
- `credentials: Mapping[str, Any]` - Current credentials containing refresh_token
**Output**: `ToolOAuthCredentials` - New credentials with updated access token
**Key Tasks**:
- Extract refresh_token from current credentials
- POST to token endpoint with refresh_token and grant_type="refresh_token"
- Return new credentials with updated access_token

#### `_validate_credentials()`
**Purpose**: Test if credentials are valid by making an API call
**Input**: `credentials: dict[str, Any]` - OAuth credentials to validate
**Output**: `None` (raises exception if invalid)
**Key Tasks**:
- Extract access_token and make test API call
- Raise `ToolProviderCredentialValidationError` if credentials are invalid

### 2. Required Imports
```python
from dify_plugin import ToolProvider
from dify_plugin.entities.oauth import ToolOAuthCredentials
from dify_plugin.errors.tool import ToolProviderCredentialValidationError, ToolProviderOAuthError
```

### 3. Accessing Credentials in Tools
In your tool's `_invoke()` method, access OAuth credentials using:
```python
access_token = self.runtime.credentials.get("access_token")
```

### 4. Provider Configuration YAML

OAuth plugins require an `oauth_schema` section with two parts:

```yaml
oauth_schema:
  client_schema:
    - name: "client_id"
      type: "secret-input"
      required: true
      url: "https://console.service.com/credentials"  # Link to where users get credentials
      label:
        en_US: "Client ID"
        zh_Hans: "客户端ID"
      placeholder:
        en_US: "Enter your OAuth Client ID"
    - name: "client_secret"
      type: "secret-input"
      required: true
      url: "https://console.service.com/credentials"
      label:
        en_US: "Client Secret"
        zh_Hans: "客户端密钥"
  credentials_schema:
    - name: "access_token"
      type: "secret-input"
      label:
        en_US: "Access Token"
    - name: "refresh_token"
      type: "secret-input"
      label:
        en_US: "Refresh Token"
```

**Key Requirements**:
- `client_schema`: Defines fields users configure (client_id, client_secret from OAuth app)
- `credentials_schema`: Defines OAuth tokens obtained through the flow (access_token, refresh_token)
- Include `url` field in client_schema to help users find where to get credentials
- Use consistent field names - these are passed to your OAuth methods as `system_credentials`

## Common Troubleshooting

### 1. 403 Forbidden Errors
- **Check API enablement**: Ensure the required APIs are enabled in the service console
- **Verify scopes**: Make sure your OAuth scopes match the API operations you're performing
- **Test user limitations**: If your app is unverified, add test users in the OAuth consent screen
- **Re-authorize**: Delete existing tokens and re-authorize with updated scopes

### 2. Redirect URI Mismatch
- **Exact match required**: The redirect URI must exactly match what's configured in the OAuth app
- **HTTPS required**: Most services require HTTPS redirect URIs
- **Check plugin ID**: Ensure the plugin ID in the redirect URI matches your actual plugin

### 3. Token Refresh Issues
- **Missing refresh token**: Ensure you request `access_type=offline` and `prompt=consent`
- **Scope changes**: When changing scopes, users need to re-authorize completely
- **Refresh token expiry**: Some services expire refresh tokens after long periods of inactivity

### 4. Development vs Production
- **Test users**: During development, add your email as a test user
- **App verification**: For production, submit your app for verification with the service provider
- **Rate limits**: Be aware of API rate limits during development and implement proper error handling

## Best Practices

1. **Security**:
   - Never log or expose access tokens
   - Use HTTPS for all OAuth flows
   - Implement proper error handling for expired tokens

2. **User Experience**:
   - Provide clear authorization instructions
   - Handle token expiry gracefully with re-authorization prompts
   - Test the complete flow from user perspective

3. **Development**:
   - Test with multiple user accounts
   - Handle edge cases (missing permissions, API errors)
   - Implement proper logging for debugging

4. **Scopes**:
   - Request minimal necessary permissions
   - Document what data your plugin accesses
   - Consider offering different permission levels

This guide provides the foundation for implementing OAuth in your Dify tool plugins. Each service has unique requirements, so always consult the specific OAuth documentation for the services you're integrating with.