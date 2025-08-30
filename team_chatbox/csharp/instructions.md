Here’s a single, copy-pasteable instruction you can give to Claude. It tells Claude exactly what to build in C# and how.

⸻

INSTRUCTION FOR CLAUDE (BUILD A WINDOWS TEAMS CLI IN C#)

You are an expert .NET 8 engineer. Create a production-ready Windows CLI app (“teams-cli”) that lets a user chat in Microsoft Teams via Microsoft Graph using device-code auth (MFA-compatible). Use C#/.NET 8, MSAL.NET for auth, MSAL Extensions for a DPAPI-protected token cache, and HttpClient to call Graph REST. Do not use preview APIs.

High-level requirements
	•	Platform: Windows 10/11, .NET 8.
	•	Auth: Device Code Flow with MSAL.NET (PublicClientApplication), honoring tenant policies/MFA.
	•	Token cache: Microsoft.Identity.Client.Extensions.Msal with DPAPI storage on Windows.
	•	Permissions (delegated): Chat.ReadBasic, Chat.ReadWrite, ChannelMessage.Send, offline_access (scopes configurable).
	•	Graph base URL: https://graph.microsoft.com/v1.0.
	•	CLI style: teams-cli <command> [subcommand] [options]. Use a mature arg parser (e.g., System.CommandLine or Spectre.Console.Cli).
	•	Logging: minimal console logging with sensible verbosity flags (-v, --debug).
	•	Resilience: handle 401 (silently refresh), 429 (respect Retry-After), 5xx (exponential backoff).
	•	Packaging: publish single-file self-contained exe for win-x64.
	•	No interactive prompts except device-code message; everything else is flags/args.

Commands & behavior
	1.	login
	•	Starts device-code auth; prints the MSAL message (URL + code).
	•	On success, cache tokens via DPAPI; print signed-in UPN.
	2.	chats ls [--top N] [--json]
	•	GET /me/chats
	•	Output: table with chatId, topic/name, type (oneOnOne/group), lastMessagePreview, lastUpdated.
	•	--json prints raw JSON.
	3.	chat send --chat <CHAT_ID> --text "<MESSAGE>" [--html]
	•	POST /chats/{id}/messages with body { "body": { "contentType": "text|html", "content": "<...>" } }.
	•	If --html set, use "html"; default "text".
	•	Print message id on success.
	4.	chat tail --chat <CHAT_ID> [--since <DELTA_URL_FILE>] [--timeout-sec 0|N]
	•	Use delta to fetch new messages:
	•	Initial call: GET /chats/{id}/messages/delta (persist returned @odata.deltaLink to a local file unless --since provided).
	•	Subsequent polls: call the stored deltaLink.
	•	Stream any newly received messages (author UPN, timestamp, content stripped to text if html).
	•	--timeout-sec controls how long to poll; 0 = run until Ctrl+C.
	•	Back off on 429/5xx with jitter.
	5.	open --chat <CHAT_ID> [--message "<URLENCODED>"]
	•	Construct Teams deep link for a 1:1/group chat and open via Process.Start().
	•	If --message is provided, include it in the deep link.
	6.	me
	•	GET /me to show displayName, userPrincipalName, id (quick sanity check).

Project layout

teams-cli/
├─ src/
│  ├─ TeamsCli/
│  │  ├─ Program.cs
│  │  ├─ Commands/
│  │  │  ├─ LoginCommand.cs
│  │  │  ├─ ChatsListCommand.cs
│  │  │  ├─ ChatSendCommand.cs
│  │  │  ├─ ChatTailCommand.cs
│  │  │  └─ OpenCommand.cs
│  │  ├─ Auth/
│  │  │  ├─ AuthService.cs          // MSAL device code + token acquisition/refresh
│  │  │  └─ TokenCache.cs           // DPAPI cache via MSAL Extensions
│  │  ├─ Graph/
│  │  │  ├─ GraphClient.cs          // wrapper over HttpClient w/ bearer, retry, helpers
│  │  │  ├─ Endpoints.cs            // URI helpers for /me/chats, /chats/{id}/messages, delta
│  │  │  └─ Models.cs               // minimal DTOs for responses we parse
│  │  ├─ DeepLinks/
│  │  │  └─ TeamsDeepLink.cs        // build chat deep links and Process.Start
│  │  ├─ Util/
│  │  │  ├─ ConsoleTable.cs
│  │  │  └─ RetryPolicy.cs
│  │  ├─ appsettings.json           // tenantId, clientId, default scopes
│  │  └─ TeamsCli.csproj
├─ README.md
└─ build/
   └─ publish.ps1

Implementation specifics
	•	AuthService.cs
	•	Use PublicClientApplicationBuilder.Create(clientId).WithAuthority($"https://login.microsoftonline.com/{tenantId}").
	•	Device code: AcquireTokenWithDeviceCode(scopes, callback).
	•	Save/read cache via Microsoft.Identity.Client.Extensions.Msal:
	•	StorageCreationPropertiesBuilder → DPAPI on Windows; store under %LOCALAPPDATA%\teams-cli\msal_cache.dat.
	•	Expose GetAccessTokenAsync(); auto-refresh on 401.
	•	GraphClient.cs
	•	Single HttpClient instance with default headers; inject token via AuthenticationHeaderValue("Bearer", accessToken).
	•	Methods:
	•	Task<JsonDocument> GetAsync(string pathOrAbsoluteUrl)
	•	Task<HttpResponseMessage> PostJsonAsync(string path, object payload)
	•	RetryPolicy:
	•	On 429: read Retry-After seconds; wait + retry (max attempts 5).
	•	On 5xx: exponential backoff with jitter (max attempts 5).
	•	Throw detailed exception with response content on final failure.
	•	Endpoints.cs
	•	Me() → /me
	•	MeChats() → /me/chats?$top={n}
	•	ChatMessages(chatId) → /chats/{chatId}/messages
	•	ChatMessagesDelta(chatId) → /chats/{chatId}/messages/delta
	•	Accept absolute deltaLink too.
	•	ChatsListCommand.cs
	•	Calls /me/chats; prints table or --json.
	•	ChatSendCommand.cs
	•	POST /chats/{id}/messages with body:

{ "body": { "contentType": "text|html", "content": "..." } }


	•	ChatTailCommand.cs
	•	If --since not provided, start with first delta call and persist @odata.deltaLink to %LOCALAPPDATA%\teams-cli\delta-{chatId}.txt.
	•	Print each new message as:

[2025-08-29 14:03:12Z] alice@contoso.com: Hello world


	•	Handle HTML → text (strip tags for console).

	•	OpenCommand.cs
	•	Build a deep link for chat and Process.Start(link).
	•	If not sure of UPN membership, still open the chat by id (if supported), else document limitation.

Configuration
	•	appsettings.json fields:

{
  "tenantId": "YOUR_TENANT_GUID_OR_DOMAIN",
  "clientId": "YOUR_PUBLIC_CLIENT_APP_ID",
  "scopes": [ "Chat.ReadBasic", "Chat.ReadWrite", "ChannelMessage.Send", "offline_access" ],
  "graphBaseUrl": "https://graph.microsoft.com/v1.0"
}


	•	Also allow env overrides: TENANT_ID, CLIENT_ID, SCOPES (comma-sep).

Build & packaging
	•	Provide README.md with:
	•	Entra ID app registration steps (public client; allow device code; delegated scopes; admin consent).
	•	dotnet build and dotnet publish:

dotnet publish src/TeamsCli/TeamsCli.csproj -c Release -r win-x64 -p:PublishSingleFile=true -p:PublishTrimmed=true --self-contained true -o dist


	•	Example usage:

teams-cli login
teams-cli chats ls --top 20
teams-cli chat send --chat <CHAT_ID> --text "Hello from CLI"
teams-cli chat tail --chat <CHAT_ID> --timeout-sec 0
teams-cli open --chat <CHAT_ID> --message "Ping from CLI"



Quality gates
	•	Add minimal unit tests for:
	•	Retry/backoff logic (simulate 429/5xx).
	•	Delta link persistence and re-use.
	•	JSON parsing for chats list.
	•	Graceful error messages for:
	•	Missing consent/scopes (explain which scope failed).
	•	403/404 on bad chat id.
	•	Network timeouts.

Deliverables
	•	Complete C# source per layout above.
	•	A working single-file EXE build instruction that I can run locally.
	•	README.md with setup, scopes, and sample commands.
	•	No external services beyond Microsoft Graph.

Please generate the full project (all files) with clear code blocks per file.
