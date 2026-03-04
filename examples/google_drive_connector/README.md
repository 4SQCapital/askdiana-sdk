# Google Drive Connector

A marketplace extension that imports Google Drive files into Ask DIANA using the `askdiana-sdk`.

## How to Run (Step by Step)

### 1. Get your Ask DIANA developer credentials

```bash
# In your Ask DIANA app:
# 1. Go to Developer Portal -> Apply for developer access
# 2. Get approved by admin
# 3. Create an API key with scopes: documents:read, documents:write, user:profile
# 4. Copy the API key (askd_...) and webhook signing secret
```

### 2. Get a Google API key

```bash
# 1. Go to https://console.cloud.google.com/
# 2. Create a project (or use existing)
# 3. Enable "Google Drive API"
# 4. Go to Credentials -> Create Credentials -> API key
# 5. Copy the API key (AIzaSy...)
# 6. (Optional) Restrict the key to Google Drive API only
```

### 3. Install dependencies

```bash
cd examples/google_drive_connector

# Install the SDK
pip install -e ../..

# Install connector dependencies
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:
```
ASKDIANA_API_KEY=askd_your_key_here
ASKDIANA_BASE_URL=http://localhost:5001    # or your Ask DIANA URL
WEBHOOK_SIGNING_SECRET=your-secret
GOOGLE_API_KEY=AIzaSy_your_key_here
PORT=5004
```

### 5. Register the extension in Ask DIANA

```bash
# Create the extension via the API (or use the Developer Portal UI):
curl -X POST http://localhost:5001/api/marketplace/extensions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Google Drive Connector",
    "slug": "google-drive-connector",
    "type": "connector",
    "visibility": "private",
    "description": "Import Google Drive files into Ask DIANA",
    "short_description": "Google Drive file sync"
  }'

# Note the extension_id from the response

# Submit a version with the manifest:
curl -X POST http://localhost:5001/api/marketplace/extensions/EXTENSION_ID/versions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0.0",
    "changelog": "Initial release",
    "webhook_url": "http://localhost:5004",
    "manifest": <contents of manifest.json>
  }'
```

Private extensions are **auto-approved** — no admin review needed.

### 6. Start the extension server

```bash
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5004
 * Debugger is active
```

### 7. Install the extension as a user

```bash
# In the Ask DIANA frontend:
# 1. Go to Extensions dialog
# 2. Find "Google Drive Connector"
# 3. Click Install
# 4. Accept the requested permissions (documents:read, documents:write, user:profile)
```

This triggers the `on_install` webhook which sets up the database schema.

### 8. Use the connector

```bash
# List files (replace INSTALL_ID with your actual install ID)
curl "http://localhost:5004/api/files?install_id=INSTALL_ID"

# Sync a file to Ask DIANA
curl -X POST http://localhost:5004/api/sync \
  -H "Content-Type: application/json" \
  -d '{"install_id": "INSTALL_ID", "file_id": "GOOGLE_DRIVE_FILE_ID"}'

# View sync history
curl "http://localhost:5004/api/sync/history?install_id=INSTALL_ID"
```

### For production: Use ngrok

```bash
ngrok http 5004
# Update webhook_url to the ngrok URL when submitting the version
```

---

## Architecture

```
Developer sets GOOGLE_API_KEY on the extension server
        |
        v
User installs extension in Ask DIANA
        |
        v
Ask DIANA sends webhook --> Extension registers SyncHistory schema
                             in ask_extensions database
        |
        v
User optionally sets root folder ID in extension settings
        |
        v
/api/files --> GoogleDriveService.list_files()
               --> Google Drive API (with server API key)
        |
        v
/api/sync --> GoogleDriveService.sync_file()
              --> Downloads from Google Drive
              --> Uploads to Ask DIANA via client.upload_document()
              --> Records sync history via client.set_data()
```

## Project Structure

```
google_drive_connector/
  app.py              # Flask routes using ExtensionApp
  drive_service.py    # GoogleDriveService (extends ConnectorService)
  google_drive.py     # Low-level Google Drive API calls
  models.py           # SyncHistory ExtModel (ask_extensions DB)
  manifest.json       # Extension manifest with settings form
  .env.example        # Environment variables template
  requirements.txt    # Python dependencies
  README.md           # This file
```

## SDK Features Used

| SDK Feature | Used For |
|-------------|----------|
| `ExtensionApp` | Flask wrapper with webhook verification, model discovery |
| `ConnectorService` | Base class with sync workflow, history tracking |
| `ExtModel` | Declare `ext_gdrive_sync_history` table in extensions DB |
| `client.upload_document()` | Upload synced files to Ask DIANA |
| `client.get_config()` | Read user's settings (root_folder_id) |
| `client.set_data()` | Store sync history records |
| `client.list_data()` | Retrieve sync history |
| `verify_webhook()` | Verify webhook signatures (via ExtensionApp) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ASKDIANA_API_KEY` | Developer API key (`askd_...`) |
| `ASKDIANA_BASE_URL` | Ask DIANA instance URL |
| `WEBHOOK_SIGNING_SECRET` | Webhook signing secret |
| `GOOGLE_API_KEY` | Google API key (server-side) |
| `PORT` | Server port (default: 5004) |
