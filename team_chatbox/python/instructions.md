BLUF: Here’s a single, copy-pasteable prompt you can give to Claude to generate a Windows-first Python Teams CLI using MSAL device-code auth (MFA-compatible), keyring token cache, and Microsoft Graph. It mirrors the C# version’s features and commands.

⸻

INSTRUCTION FOR CLAUDE (BUILD A WINDOWS TEAMS CLI IN PYTHON)

You are an expert Python engineer. Create a production-ready Windows-first CLI app named teams-cli that lets a user chat in Microsoft Teams via Microsoft Graph using device-code OAuth (MFA-compatible). Use Python 3.11+, msal for auth, requests for HTTP, keyring for secure token caching on Windows (DPAPI via Windows Credential Manager), and argparse or typer for the CLI. Avoid preview Graph APIs.

High-Level Requirements
	•	Platform: Windows 10/11 (+ works cross-platform if keyring available).
	•	Auth: Device Code Flow (MSAL PublicClientApplication). Must honor tenant MFA/conditional access.
	•	Token Cache: Store access/refresh tokens in keyring (service="teams-cli", account=user@domain), fall back to local JSON if keyring unavailable.
	•	Permissions (delegated): Chat.ReadBasic, Chat.ReadWrite, ChannelMessage.Send, offline_access (configurable).
	•	Graph base URL: https://graph.microsoft.com/v1.0.
	•	CLI UX: teams-cli <command> [options]. Non-interactive except the device-code message.
	•	Resilience: Automatic refresh on 401; 429 obey Retry-After; 5xx use exponential backoff with jitter.
	•	Output: Human-readable tables by default; --json to emit raw JSON.
	•	Packaging: Provide PyInstaller spec to build a single EXE for win-x64.
	•	No preview APIs. Clean error messages.

Commands & Behavior
	1.	login
	•	Starts device-code auth; print MSAL message (verification URL + code).
	•	On success, store token in keyring; print userPrincipalName from /me.
	2.	me
	•	GET /me; display displayName, userPrincipalName, id.
	3.	chats ls [--top N] [--json]
	•	GET /me/chats?$top={N}; table columns: chatId, type (oneOnOne/group), topic/name, lastMessagePreview, lastUpdated.
	•	--json prints full JSON.
	4.	chat send --chat <CHAT_ID> --text "<MESSAGE>" [--html]
	•	POST /chats/{id}/messages with body:

{ "body": { "contentType": "text|html", "content": "..." } }


	•	Print message id on success.

	5.	chat tail --chat <CHAT_ID> [--since <PATH_TO_DELTA_FILE>] [--timeout-sec 0|N]
	•	Use delta to stream new messages:
	•	First call: GET /chats/{id}/messages/delta → save @odata.deltaLink to %LOCALAPPDATA%\teams-cli\delta-{chatId}.txt unless --since overrides.
	•	Subsequent polls: call the stored deltaLink.
	•	Print new messages as:

[2025-08-29 14:03:12Z] alice@contoso.com: Hello world


	•	Strip HTML if needed for console display.
	•	Back off on 429/5xx; --timeout-sec 0 means run until Ctrl+C.

	6.	open --chat <CHAT_ID> [--message "<URLENCODED>"]
	•	Build a Teams deep link for the chat and open it:
	•	Use webbrowser.open() on Windows (will launch Teams desktop if registered, otherwise web).
	•	If --message provided, include it in the link.

Project Layout

teams-cli/
├─ src/
│  └─ teams_cli/
│     ├─ __init__.py
│     ├─ app.py                     # main entry (argparse/typer)
│     ├─ config.py                  # read appsettings.json + env overrides
│     ├─ auth.py                    # MSAL device code, keyring cache, refresh on 401
│     ├─ graph.py                   # Http client wrapper (requests + retry/backoff)
│     ├─ endpoints.py               # URL builders: /me, /me/chats, /chats/{id}/messages, delta
│     ├─ commands/
│     │  ├─ login.py
│     │  ├─ me.py
│     │  ├─ chats_ls.py
│     │  ├─ chat_send.py
│     │  └─ chat_tail.py
│     ├─ deeplink.py                # build/open chat deep links
│     ├─ printing.py                # table rendering (width-safe), JSON passthrough
│     └─ storage.py                 # delta link persistence under %LOCALAPPDATA%
├─ appsettings.json                 # tenantId, clientId, scopes, graphBaseUrl
├─ pyproject.toml                   # build system (hatchling/poetry); deps: msal, requests, keyring, typer(or argparse)
├─ requirements.txt                 # alternative to pyproject (msal, requests, keyring, typer)
├─ README.md
├─ LICENSE
└─ build/
   ├─ pyinstaller.spec
   └─ make_exe.ps1

Implementation Details

Dependencies
	•	msal, requests, keyring, typer (or argparse), colorama (optional for Windows colors).

Configuration
	•	appsettings.json:

{
  "tenantId": "YOUR_TENANT_GUID_OR_DOMAIN",
  "clientId": "YOUR_PUBLIC_CLIENT_APP_ID",
  "scopes": ["Chat.ReadBasic","Chat.ReadWrite","ChannelMessage.Send","offline_access"],
  "graphBaseUrl": "https://graph.microsoft.com/v1.0"
}


	•	Allow env overrides: TENANT_ID, CLIENT_ID, SCOPES (comma-sep), GRAPH_BASE_URL.

auth.py
	•	Create PublicClientApplication(client_id, authority=f"https://login.microsoftonline.com/{tenant}").
	•	Try loading cached token from keyring.get_password("teams-cli", upn_or_hint); if missing/expired, run device flow:

flow = app.initiate_device_flow(scopes=SCOPES)
print(flow["message"])
token = app.acquire_token_by_device_flow(flow)


	•	On success, keyring.set_password("teams-cli", upn, json.dumps(token)).
	•	Provide get_access_token() that refreshes when 401 occurs (re-acquire using refresh token if present; else new device flow).
	•	Extract preferred_username or /me UPN for keyring account name.

graph.py
	•	One requests.Session() with default headers.
	•	request(method, url, json=None) wrapper that:
	•	Injects Authorization: Bearer <token>.
	•	On 401 once: refresh token via auth, retry.
	•	On 429: read Retry-After seconds, sleep, retry (max 5).
	•	On 5xx: exponential backoff with jitter (max 5).
	•	Raise an error with response text on final failure.

endpoints.py
	•	Helpers that return full URLs for:
	•	/me
	•	/me/chats?$top={n}
	•	/chats/{chatId}/messages
	•	/chats/{chatId}/messages/delta
	•	Accept absolute deltaLink passthrough.

commands/
	•	login.py: run device flow, print signed-in UPN.
	•	me.py: call /me; print key properties.
	•	chats_ls.py: call /me/chats; render table or --json.
	•	chat_send.py: POST /chats/{id}/messages with text/html content.
	•	chat_tail.py:
	•	If --since not given, load or create %LOCALAPPDATA%\teams-cli\delta-{chatId}.txt.
	•	First call to delta returns messages + @odata.deltaLink; print new ones and save the deltaLink.
	•	Subsequent loops call the stored deltaLink and print incremental results.
	•	Respect --timeout-sec.

deeplink.py
	•	Build a Teams chat deep link and webbrowser.open(link) (Windows associates Teams v2 / protocol handler; otherwise opens web).

printing.py
	•	Column-safe console table (fallback to simple tab-separated if terminal width unknown).
	•	--json prints json.dumps(response, indent=2).

storage.py
	•	Resolve %LOCALAPPDATA%\teams-cli\ folder.
	•	Save/read delta links and optional settings files.

Testing & Quality
	•	Unit tests (pytest) for:
	•	Backoff logic on 429/5xx (mock responses).
	•	Delta link persistence & reuse.
	•	Minimal parsing (e.g., chats list rows).
	•	Manual test checklist:
	•	First-time login (device code shows and succeeds).
	•	me, chats ls, chat send, chat tail happy paths.
	•	Throttling behavior simulation.

Packaging (PyInstaller)
	•	Provide build/pyinstaller.spec and build/make_exe.ps1:

pyinstaller -F -n teams-cli -i NONE --clean .\src\teams_cli\app.py
# Output: dist\teams-cli.exe


	•	Document required VC++ runtime if any; otherwise pure Python should bundle.

README.md (include)
	•	Prereqs: Python 3.11+, pip install -r requirements.txt
	•	Entra ID registration steps: create app, enable Allow public client flows, add delegated Graph permissions Chat.ReadBasic, Chat.ReadWrite, ChannelMessage.Send, offline_access, grant admin consent, capture tenantId and clientId.
	•	Config: edit appsettings.json or set env vars.
	•	Usage:

teams-cli login
teams-cli me
teams-cli chats ls --top 20
teams-cli chat send --chat <CHAT_ID> --text "Hello from Python CLI"
teams-cli chat tail --chat <CHAT_ID> --timeout-sec 0
teams-cli open --chat <CHAT_ID> --message "Ping from CLI"



Deliverables
	•	Full source tree with modules above.
	•	requirements.txt (or pyproject.toml) with pinned versions.
	•	appsettings.json template.
	•	build/pyinstaller.spec and build/make_exe.ps1.
	•	Tests (tests/) for retry/delta/storage logic.
	•	Clear README with setup, scopes, examples, and troubleshooting.

Generate the complete project with code files per layout, ready to run.
