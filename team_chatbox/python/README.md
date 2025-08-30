# Teams CLI - Microsoft Teams Command Line Interface

A Windows-first Python CLI application for Microsoft Teams that uses MSAL device code authentication to interact with Microsoft Graph API. Send messages, list chats, tail conversations, and open Teams deep links directly from the command line.

## Features

- **Device Code Authentication**: MFA-compatible OAuth flow using MSAL
- **Secure Token Storage**: Uses Windows Credential Manager (keyring) with fallback to encrypted local storage
- **Chat Management**: List chats, send messages, stream new messages with delta queries
- **Deep Link Support**: Open Teams chats directly in desktop or web app
- **Robust Error Handling**: Automatic token refresh, rate limiting respect, exponential backoff
- **Rich Output**: Formatted tables and colored console output with JSON fallback
- **Cross-Platform**: Works on Windows, macOS, and Linux (keyring support varies)

## Prerequisites

- **Python 3.11+** (recommended Python 3.12)
- **Microsoft 365/Azure AD account** with Teams access
- **Azure AD App Registration** (see setup instructions below)

## Installation

### Option 1: Install from Source

```bash
git clone <repository-url>
cd teams-cli
pip install -r requirements.txt
```

### Option 2: Build Executable (Windows)

```powershell
# Install dependencies first
pip install -r requirements.txt

# Build executable using PowerShell
cd build
.\make_exe.ps1

# Or using batch file
.\make_exe.bat
```

The executable will be created at `build/dist/teams-cli.exe`.

## Azure AD App Registration Setup

1. **Register Application**:
   - Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
   - Click "New registration"
   - Name: `teams-cli` (or your preferred name)
   - Supported account types: Choose appropriate option for your organization
   - Redirect URI: Leave blank for public client applications

2. **Configure as Public Client**:
   - Go to Authentication → Advanced settings
   - Enable "Allow public client flows": **Yes**

3. **Add Microsoft Graph Permissions**:
   - Go to API permissions → Add a permission → Microsoft Graph → Delegated permissions
   - Add these permissions:
     - `Chat.ReadBasic` - Read basic chat information
     - `Chat.ReadWrite` - Read and write chat messages
     - `ChannelMessage.Send` - Send messages to channels
     - `offline_access` - Maintain access to data you have given it access to

4. **Grant Admin Consent** (if required by your organization):
   - Click "Grant admin consent for [Your Organization]"

5. **Copy Configuration**:
   - Copy the **Application (client) ID**
   - Copy your **Directory (tenant) ID** or use your domain name

## Configuration

Edit `appsettings.json` with your Azure AD app details:

```json
{
  "tenantId": "your-tenant-id-or-domain.onmicrosoft.com",
  "clientId": "your-application-client-id",
  "scopes": ["Chat.ReadBasic", "Chat.ReadWrite", "ChannelMessage.Send", "offline_access"],
  "graphBaseUrl": "https://graph.microsoft.com/v1.0"
}
```

### Environment Variable Overrides

You can override configuration using environment variables:

```bash
set TENANT_ID=your-tenant-id
set CLIENT_ID=your-client-id
set SCOPES=Chat.ReadBasic,Chat.ReadWrite,ChannelMessage.Send,offline_access
set GRAPH_BASE_URL=https://graph.microsoft.com/v1.0
```

## Usage

### First Time Setup

```bash
# Authenticate with Microsoft Teams
teams-cli login
```

This will:
1. Display a device code and verification URL
2. Open your browser to https://microsoft.com/devicelogin
3. Enter the device code shown in the terminal
4. Complete authentication with your Microsoft 365 account
5. Store the token securely in Windows Credential Manager

### Available Commands

#### Get Current User Info
```bash
teams-cli me
teams-cli me --json  # Raw JSON output
```

#### List Teams Chats
```bash
teams-cli chats ls
teams-cli chats ls --top 20     # Limit to 20 chats
teams-cli chats ls --json       # Raw JSON output
```

#### Send Message to Chat
```bash
teams-cli chat send --chat "CHAT_ID" --text "Hello from CLI!"
teams-cli chat send --chat "CHAT_ID" --text "<b>Bold text</b>" --html
```

#### Stream Messages from Chat (Tail)
```bash
# Stream messages until Ctrl+C
teams-cli chat tail --chat "CHAT_ID"

# Stream with timeout
teams-cli chat tail --chat "CHAT_ID" --timeout-sec 300

# Use custom delta file location
teams-cli chat tail --chat "CHAT_ID" --since "C:\\path\\to\\custom-delta.txt"
```

#### Open Teams Chat
```bash
# Open in Teams desktop app (if available) or web
teams-cli open --chat "CHAT_ID"

# Open with pre-filled message
teams-cli open --chat "CHAT_ID" --message "Hello from CLI"
```

### Finding Chat IDs

To find a chat ID, first list your chats:

```bash
teams-cli chats ls
```

The output will show chat IDs (truncated in table view). Use `--json` to see full IDs:

```bash
teams-cli chats ls --json
```

## Data Storage

### Token Storage
- **Windows**: Windows Credential Manager (secure DPAPI encryption)
- **macOS/Linux**: System keyring (varies by platform)
- **Fallback**: Encrypted local file in user directory

### Delta Links
Delta links for chat tailing are stored in:
- **Windows**: `%LOCALAPPDATA%\teams-cli\delta-{chatId}.txt`
- **macOS/Linux**: `~/.teams-cli/delta-{chatId}.txt`

## Error Handling & Resilience

The CLI automatically handles:
- **Token Expiration**: Automatic refresh using refresh tokens
- **Rate Limiting**: Respects `Retry-After` headers from Microsoft Graph
- **Network Issues**: Exponential backoff with jitter for 5xx errors
- **Authentication Failures**: Clear error messages with remediation steps

## Troubleshooting

### Authentication Issues

```bash
# Clear stored tokens and re-authenticate
teams-cli login
```

### Permission Errors
Ensure your Azure AD app has the required Microsoft Graph permissions and admin consent is granted.

### Rate Limiting
The CLI automatically handles rate limits, but if you encounter persistent issues:
- Reduce frequency of API calls
- Check if other applications are using the same app registration

### Keyring Issues
If keyring fails to save tokens:
- The CLI will fall back to local file storage
- Check Windows Credential Manager for stored entries under "teams-cli"

### Network/Proxy Issues
For corporate networks with proxies, ensure your Python environment respects system proxy settings.

## Development

### Project Structure
```
teams-cli/
├── src/teams_cli/
│   ├── __init__.py
│   ├── app.py              # Main CLI entry point (Typer)
│   ├── config.py           # Configuration management
│   ├── auth.py             # MSAL authentication & token management
│   ├── graph.py            # Microsoft Graph API client
│   ├── endpoints.py        # URL builders for Graph endpoints
│   ├── deeplink.py         # Teams deep link functionality
│   ├── printing.py         # Console output formatting
│   ├── storage.py          # Local file storage utilities
│   └── commands/           # Command implementations
│       ├── login.py
│       ├── me.py
│       ├── chats_ls.py
│       ├── chat_send.py
│       └── chat_tail.py
├── tests/                  # Unit tests (pytest)
├── build/                  # PyInstaller build scripts
├── appsettings.json        # Configuration template
├── requirements.txt        # Python dependencies
└── README.md
```

### Running Tests
```bash
pip install pytest pytest-asyncio pytest-mock
pytest tests/
```

### Building Executable
```powershell
cd build
.\make_exe.ps1          # PowerShell script
# or
.\make_exe.bat          # Batch file alternative
```

## Security Considerations

- Tokens are stored securely using Windows Credential Manager
- No credentials are logged or displayed in console output
- HTTPS is enforced for all Microsoft Graph API calls
- Minimal required permissions are requested

## Dependencies

- **msal**: Microsoft Authentication Library for device code flow
- **requests**: HTTP client for Microsoft Graph API calls  
- **keyring**: Cross-platform secure credential storage
- **typer**: Modern CLI framework with type hints
- **rich**: Rich text and formatting for console output
- **colorama**: Cross-platform colored terminal text support

## License

MIT License - see LICENSE file for details.

## Support

For issues and feature requests, please create an issue in the project repository.

## Limitations

- Uses Microsoft Graph v1.0 endpoints (no preview/beta APIs)
- Designed primarily for Windows (but works cross-platform)
- Requires internet connectivity for Microsoft Graph API access
- Subject to Microsoft Graph API rate limits and service limits