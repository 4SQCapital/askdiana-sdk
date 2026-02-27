# Google Drive Connector

A full marketplace extension that connects Google Drive to Ask DIANA. Users can browse their Drive files and sync them into their Ask DIANA knowledge base.

## What it does

- **`extension.installed`** — Saves the install context (user, tenant, scopes)
- **`extension.uninstalled`** — Cleans up stored accounts and sync history
- **OAuth flow** — Users connect their Google account via OAuth 2.0
- **File browser** — Lists files and folders from the connected Google Drive
- **Sync** — Downloads files from Drive and uploads them to Ask DIANA via the Extension API

## Prerequisites

1. **Ask DIANA developer account** with an API key (`askd_...`) that has `documents:write` scope
2. **Google Cloud Console project** with OAuth 2.0 credentials

### Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **Google Drive API**
4. Go to **Credentials** > **Create Credentials** > **OAuth client ID**
5. Application type: **Web application**
6. Add authorized redirect URI: `https://<your-ngrok-url>/oauth/callback`
7. Copy the **Client ID** and **Client Secret**

## Setup

```bash
cd examples/google_drive_connector
pip install -r requirements.txt

# If the SDK isn't installed globally:
pip install -e ../..

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your credentials
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ASKDIANA_API_KEY` | Your developer API key (`askd_...`) |
| `ASKDIANA_BASE_URL` | Ask DIANA instance URL |
| `WEBHOOK_SIGNING_SECRET` | Webhook signing secret from developer portal |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `EXTENSION_BASE_URL` | Your server's public URL (ngrok for dev) |
| `PORT` | Server port (default: 5004) |
| `DATABASE_PATH` | SQLite database path (default: ./connector.db) |

## Running

```bash
# Start the extension
python app.py

# In another terminal, expose with ngrok
ngrok http 5004
```

Update `EXTENSION_BASE_URL` in `.env` with the ngrok URL, and update the redirect URI in Google Cloud Console.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhooks/install` | Handle install webhook |
| POST | `/webhooks/uninstall` | Handle uninstall webhook |
| POST | `/webhooks/events` | Handle event webhooks |
| GET | `/oauth/start?install_id=<uuid>` | Start Google OAuth flow |
| GET | `/oauth/callback` | Google OAuth callback |
| GET | `/api/accounts?install_id=<uuid>` | List connected Google accounts |
| GET | `/api/files?install_id=<uuid>&account_id=<id>` | List Google Drive files |
| POST | `/api/sync` | Sync a file to Ask DIANA |
| GET | `/api/sync/history?install_id=<uuid>` | Get sync history |
| GET | `/health` | Health check |

### Sync Request

```bash
curl -X POST http://localhost:5004/api/sync \
  -H "Content-Type: application/json" \
  -d '{
    "install_id": "uuid-from-webhook",
    "account_id": 1,
    "file_id": "google-drive-file-id"
  }'
```

## Extension Manifest

See `manifest.json` for the full manifest. Register this extension in the Ask DIANA marketplace with:

- **Permissions**: `documents:read`, `documents:write`, `user:profile`
- **Webhook URLs**: Point to your server's `/webhooks/install`, `/webhooks/uninstall`, `/webhooks/events`

## Architecture

```
User installs extension in Ask DIANA
        │
        ▼
Ask DIANA sends webhook ──► Extension saves install context
        │
        ▼
User clicks "Connect Google Drive"
        │
        ▼
Extension redirects to Google OAuth
        │
        ▼
User authorizes ──► Extension stores tokens in SQLite
        │
        ▼
User browses files via /api/files
        │
        ▼
User selects file to sync
        │
        ▼
Extension downloads from Google Drive
        │
        ▼
Extension uploads to Ask DIANA via POST /api/ext/documents/upload
        │
        ▼
Document appears in user's Ask DIANA knowledge base
```

## Required Scopes

| Scope | Used for |
|-------|----------|
| `documents:read` | Listing existing documents |
| `documents:write` | Uploading synced files to Ask DIANA |
| `user:profile` | Identifying the connected user |
