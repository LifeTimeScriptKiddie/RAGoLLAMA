# Teams CLI

A production-ready Windows CLI application for chatting in Microsoft Teams via Microsoft Graph API using device-code authentication.

## Features

- **Authentication**: Device Code Flow with MSAL.NET (MFA compatible)
- **Secure Token Storage**: DPAPI-protected token cache on Windows
- **Chat Operations**: List chats, send messages, tail messages in real-time
- **Teams Integration**: Open chats directly in Teams app
- **Resilient**: Automatic retry with exponential backoff for 429/5xx errors

## Prerequisites

- Windows 10/11
- .NET 8.0 Runtime
- Microsoft Teams application (for deep links)
- Azure AD application registration

## Azure AD App Registration

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
2. Click "New registration"
3. Configure:
   - **Name**: `teams-cli`
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: Leave empty (public client)
4. After creation, go to **Authentication**:
   - Click "Add a platform" → "Mobile and desktop applications"
   - Check "https://login.microsoftonline.com/common/oauth2/nativeclient"
   - Enable "Allow public client flows": Yes
5. Go to **API permissions**:
   - Click "Add a permission" → Microsoft Graph → Delegated permissions
   - Add these permissions:
     - `Chat.ReadBasic`
     - `Chat.ReadWrite`
     - `ChannelMessage.Send`
     - `offline_access`
   - Click "Grant admin consent" (if you're an admin)
6. Note down:
   - **Application (client) ID** from the Overview page
   - **Directory (tenant) ID** from the Overview page

## Configuration

1. Open `src/TeamsCli/appsettings.json`
2. Replace the placeholder values:
   ```json
   {
     "tenantId": "your-tenant-id-here",
     "clientId": "your-client-id-here",
     "scopes": [
       "Chat.ReadBasic",
       "Chat.ReadWrite", 
       "ChannelMessage.Send",
       "offline_access"
     ],
     "graphBaseUrl": "https://graph.microsoft.com/v1.0"
   }
   ```

Alternatively, set environment variables:
- `TENANT_ID`: Your tenant ID
- `CLIENT_ID`: Your application client ID  
- `SCOPES`: Comma-separated list of scopes

## Build & Run

### Development
```bash
cd src/TeamsCli
dotnet run -- login
```

### Production Build
```bash
dotnet publish src/TeamsCli/TeamsCli.csproj -c Release -r win-x64 -p:PublishSingleFile=true -p:PublishTrimmed=true --self-contained true -o dist
```

Or use the provided PowerShell script:
```powershell
.\build\publish.ps1
```

This creates a single-file executable at `dist/teams-cli.exe`.

## Usage

### Authentication
```bash
teams-cli login
```
Follow the device code instructions to authenticate.

### List Chats
```bash
# List all chats
teams-cli chats ls

# List top 10 chats  
teams-cli chats ls --top 10

# Output raw JSON
teams-cli chats ls --json
```

### Send Messages
```bash
# Send text message
teams-cli chat send --chat "CHAT_ID" --text "Hello from CLI!"

# Send HTML message
teams-cli chat send --chat "CHAT_ID" --text "<b>Bold text</b>" --html
```

### Tail Messages (Real-time)
```bash
# Tail messages indefinitely
teams-cli chat tail --chat "CHAT_ID" --timeout-sec 0

# Tail for 60 seconds
teams-cli chat tail --chat "CHAT_ID" --timeout-sec 60

# Resume from specific delta file
teams-cli chat tail --chat "CHAT_ID" --since "path/to/delta-file.txt"
```

### Open in Teams
```bash
# Open chat in Teams app
teams-cli open --chat "CHAT_ID"

# Open with pre-filled message
teams-cli open --chat "CHAT_ID" --message "Hello!"
```

### User Information
```bash
teams-cli me
```

## File Locations

- **Token cache**: `%LOCALAPPDATA%\teams-cli\msal_cache.dat`
- **Delta links**: `%LOCALAPPDATA%\teams-cli\delta-{chatId}.txt`

## Error Handling

The CLI provides graceful error handling for:
- Missing or invalid authentication
- Insufficient permissions (403)
- Rate limiting (429) with automatic retry
- Server errors (5xx) with exponential backoff
- Network timeouts
- Invalid chat IDs (404)

## Troubleshooting

### "No authenticated account found"
Run `teams-cli login` to authenticate.

### "Interactive authentication required"  
Your token has expired. Run `teams-cli login` again.

### "Insufficient privileges" (403)
Ensure your Azure AD app has the required permissions and admin consent has been granted.

### "Chat not found" (404)
Verify the chat ID is correct. Use `teams-cli chats ls` to see available chats.

### Deep links not working
Ensure Microsoft Teams desktop app is installed and set as the default handler for `msteams://` URLs.

## Development

### Project Structure
```
src/TeamsCli/
├── Auth/                   # MSAL authentication & token cache
├── Commands/              # CLI command implementations  
├── Graph/                 # Microsoft Graph client & models
├── DeepLinks/            # Teams deep link generation
├── Util/                 # Utilities (retry policy, console table)
├── Program.cs            # Main entry point & command parsing
└── appsettings.json      # Configuration
```

### Dependencies
- `Microsoft.Identity.Client` - MSAL authentication
- `Microsoft.Identity.Client.Extensions.Msal` - Token cache
- `System.CommandLine` - Command line parsing
- `System.Text.Json` - JSON serialization

## License

This project is provided as-is for demonstration purposes.