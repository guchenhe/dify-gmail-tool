# Privacy Notice - Gmail Plugin

## Overview

This privacy notice explains how the Gmail plugin for Dify processes your personal data when you use it to connect and interact with your Gmail account.

## Data Accessed

### Gmail Account Data
When you authorize this plugin, we access:

- **Email Messages**: Subject lines, sender/recipient information, dates, email content (body), and message metadata
- **Email Labels**: Gmail labels and categories associated with your messages
- **Thread Information**: Gmail conversation threading data
- **User Profile**: Basic Gmail profile information (used only for authentication validation)

### Authentication Data
- **OAuth Tokens**: Access tokens and refresh tokens provided by Google's OAuth 2.0 service
- **Client Credentials**: Google Client ID and Client Secret (configured by system administrators)

## Data Storage and Retention

### Local Processing
- **Real-time Processing**: Email data is retrieved and processed in real-time upon request
- **No Permanent Storage**: Email content is not permanently stored by the plugin
- **Temporary Processing**: Data exists only temporarily during active processing sessions

### Authentication Credentials
- **Token Storage**: OAuth access and refresh tokens are stored securely within Dify's credential management system
- **Token Refresh**: Tokens are automatically refreshed as needed to maintain access
- **Credential Validation**: Tokens are periodically validated against Google's services

## Third-Party Data Sharing

### Google Services
This plugin integrates with the following Google services:

#### Gmail API (`gmail.googleapis.com`)
- **Purpose**: To retrieve and search your email messages
- **Data Shared**: OAuth tokens for authentication
- **Scope**: Read-only access to your Gmail account (`https://www.googleapis.com/auth/gmail.readonly`)

#### Google OAuth 2.0 (`accounts.google.com`, `oauth2.googleapis.com`)
- **Purpose**: To authenticate and authorize access to your Gmail account
- **Data Shared**: Client credentials and authorization codes
- **Security**: Uses industry-standard OAuth 2.0 protocol

### Data Protection Measures
- **Read-Only Access**: The plugin only requests read-only permissions to your Gmail account
- **Encrypted Transmission**: All data transmission occurs over HTTPS/TLS encryption
- **Token Security**: OAuth tokens are handled securely and never exposed in logs or user interfaces

---

*Last Updated: [Current Date]*
*Plugin Version: 0.0.1*
