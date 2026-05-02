# Ask DIANA Extension SDK

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Python SDK for building extensions that integrate with [Ask DIANA](https://askdiana.ai).

## Prerequisites

- Python 3.8+
- An Ask DIANA developer account and API key (`askd_...` format)
- SSH access to the `4SQCapital/askdiana-sdk` repository
- A publicly reachable HTTPS URL for webhook delivery (use [ngrok](https://ngrok.com) during local development)

## Installation

```bash
# From GitHub (recommended)
pip install "git+ssh://git@github.com/4SQCapital/askdiana-sdk.git#egg=askdiana[app]"

# Core only — no Flask dependency (API client, models, webhooks)
pip install "git+ssh://git@github.com/4SQCapital/askdiana-sdk.git#egg=askdiana"

# From local source (editable mode — changes take effect immediately)
pip install -e ".[app]"
```

The `[app]` extra installs Flask and its dependencies. Required for `ExtensionApp` and
the structured extension layout. Omit it if you only need the API client or webhook
verification inside an existing web framework (Django, FastAPI, etc.).

### Local environment setup

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your actual API key and settings
```

> **Never commit `.env` files.** The `.gitignore` already excludes them.
> Share `.env.example` with placeholder values instead.

## Quick Start

### 1. Set up webhook handling

```python
import os
from flask import Flask, request, jsonify
from askdiana import verify_bearer_token, WebhookVerificationError

app = Flask(__name__)
API_KEY = os.environ.get("ASKDIANA_API_KEY", "")

@app.route("/webhooks", methods=["POST"])
def handle_webhook():
    try:
        verify_bearer_token(
            authorization_header=request.headers.get("Authorization", ""),
            expected_key=API_KEY,
        )
    except WebhookVerificationError as e:
        return jsonify({"error": str(e)}), 401

    event = request.headers.get("X-AskDiana-Event")
    body = request.get_json()
    print(f"Event: {event}, Data: {body['data']}")

    return jsonify({"ok": True}), 200
```

### 2. Call the Extension API

```python
import os
from askdiana import AskDianaClient

client = AskDianaClient(
    api_key=os.environ["ASKDIANA_API_KEY"],
    base_url="https://app.askdiana.ai",
)

install_id = "uuid-from-webhook-payload"

# List user's documents (requires documents:read scope)
docs = client.list_documents(install_id)
for doc in docs["documents"]:
    print(f"{doc['file_name']} ({doc['file_size']} bytes)")

# Get user profile (requires user:profile scope)
profile = client.get_user_profile(install_id)
print(f"User: {profile['user']['name']}")

# Get install config (no scope required) — reads settings saved by the user
config = client.get_config(install_id)
api_key = client.get_config(install_id, key="api_key")

# Upload a document (requires documents:write scope)
with open("report.pdf", "rb") as f:
    result = client.upload_document(
        install_id,
        file_content=f.read(),
        file_name="report.pdf",
        source_type="google_drive",
    )
print(f"Uploaded: {result['document']['id']}")
```

### 3. Error handling

```python
import requests
from askdiana import AskDianaClient

client = AskDianaClient(api_key=os.environ["ASKDIANA_API_KEY"])

try:
    docs = client.list_documents(install_id)
except requests.HTTPError as e:
    if e.response.status_code == 403:
        print("Missing required scope — check your extension's granted scopes")
    elif e.response.status_code == 404:
        print("Install not found")
    else:
        print(f"API error {e.response.status_code}: {e.response.text}")
except RuntimeError as e:
    print(f"Unexpected response: {e}")
```

### 4. Store and retrieve data

```python
# Store a value (any JSON-serializable data)
client.set_data(install_id, namespace="settings", key="theme",
                value={"color": "blue", "font_size": 14})

# Retrieve it
result = client.get_data(install_id, "settings", "theme")
print(result["data"]["value"])  # {"color": "blue", "font_size": 14}

# List all keys in a namespace
all_settings = client.list_data(install_id, "settings")
for item in all_settings["data"]:
    print(f"{item['key']}: {item['value']}")

# Delete a key
client.delete_data(install_id, "settings", "theme")
```

### 5. Define custom database tables

```python
from askdiana import ExtModel, StringField, IntegerField, DateTimeField, JsonField

class SyncHistory(ExtModel):
    __tablename__ = "ext_myext_sync_history"

    id = StringField(primary_key=True, max_length=36)
    install_id = StringField(max_length=36, nullable=False)
    file_name = StringField(max_length=500, nullable=False)
    status = StringField(max_length=50, nullable=False)
    synced_at = DateTimeField(nullable=True)
    metadata = JsonField(nullable=True)

# Register and create the table in one call
SyncHistory.setup(client, install_id, version="1.0.0")

# Or step by step:
SyncHistory.register(client, install_id, version="1.0.0")
SyncHistory.apply(client, install_id)
```

Available field types:

| Field | DB Type | Notes |
|-------|---------|-------|
| `StringField(max_length=N)` | `VARCHAR(N)` | Default max_length: 255 |
| `TextField()` | `TEXT` | Unlimited text |
| `IntegerField()` | `INT` | |
| `FloatField()` | `FLOAT` | |
| `BooleanField()` | `TINYINT(1)` | |
| `DateTimeField()` | `DATETIME` | |
| `DateField()` | `DATE` | |
| `JsonField()` | `JSON` | Arbitrary JSON data |

Table names **must** start with `ext_` and have at least one primary key column.

Register multiple models at once:

```python
from askdiana import register_all_models

register_all_models(client, install_id, "1.0.0", SyncHistory, UserSettings, Accounts)
```

### 6. Structured extension layout (recommended)

```bash
askdiana init my_extension  # scaffolds project structure
cd my_extension
```

This creates:

```
my_extension/
├── app.py              # ExtensionApp entry point
├── manifest.json
├── .env.example
├── requirements.txt
├── models/             # ExtModel subclasses (auto-discovered)
│   └── task.py
├── services/           # Business logic (ExtensionService subclasses)
│   └── task_service.py
├── controllers/        # Flask Blueprints (auto-discovered)
│   └── tasks.py
└── views/              # UI templates (reserved)
```

**app.py:**

```python
from askdiana import ExtensionApp

app = ExtensionApp(__name__)

@app.flask.route("/webhooks/install", methods=["POST"])
def on_install():
    from flask import request, jsonify
    app.verify_request()
    body = request.get_json()
    install_id = body["data"]["install_id"]
    app.setup_models(install_id, version="1.0.0")
    return jsonify({"ok": True}), 200

if __name__ == "__main__":
    app.run(port=5000)
```

`ExtensionApp` automatically:
- Creates an `AskDianaClient` from `ASKDIANA_API_KEY` env var
- Discovers `ExtModel` subclasses in `models/`
- Discovers and registers Flask Blueprints in `controllers/`
- Adds a `GET /health` endpoint
- Verifies webhook Bearer tokens via `app.verify_request()`

**Services** extend `ExtensionService`:

```python
from askdiana import ExtensionService

class TaskService(ExtensionService):
    def create_task(self, install_id, title):
        import uuid
        note_id = str(uuid.uuid4())
        self.client.set_data(install_id, "tasks", note_id, {"title": title})
```

**Controllers** use decorators:

```python
from flask import Blueprint, g, jsonify
from askdiana.controller import install_id_required

tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.route("/api/tasks", methods=["GET"])
@install_id_required
def list_tasks():
    # g.install_id is automatically extracted from the request
    return jsonify({"tasks": []}), 200
```

### 7. AI chat extensions (ChatService)

```python
from askdiana import ChatService

class GeminiChatService(ChatService):
    def respond(self, install_id, message, history=None, chat_id=None, **kwargs):
        import google.generativeai as genai
        # get_api_key() reads from install config (user settings) then data store
        genai.configure(api_key=self.get_api_key(install_id))
        model = genai.GenerativeModel("gemini-2.0-flash")
        return model.generate_content(message).text

svc = GeminiChatService(app.client)
svc.register_routes(app)  # registers POST /api/chat
```

### 8. File connector extensions (ConnectorService)

```python
from askdiana import ConnectorService

class GoogleDriveService(ConnectorService):
    source_type = "google_drive"
    provider_name = "google_drive"

    def get_auth_url(self, install_id, redirect_uri): ...
    def handle_auth_callback(self, install_id, code, redirect_uri): ...
    def get_auth_status(self, install_id): ...
    def disconnect(self, install_id): ...
    def list_files(self, install_id, folder_id=None, page_token=None): ...
    def download_file(self, file_id, **kwargs): ...

svc = GoogleDriveService(app.client)
svc.register_routes(app)  # registers all OAuth + sync routes
```

Routes registered by `register_routes()`:

| Route | Method | Description |
|-------|--------|-------------|
| `/api/auth/status` | GET | OAuth connection status |
| `/api/auth/url` | GET | OAuth authorization URL |
| `/api/auth/callback` | POST | Exchange code for tokens |
| `/api/auth/disconnect` | POST | Revoke tokens |
| `/api/files` | GET | List files |
| `/api/sync` | POST | Download + upload a file to Ask DIANA |

## CLI Reference

```bash
askdiana init my_extension              # Scaffold full project
askdiana scaffold model TaskTracker     # Generate models/task_tracker.py
askdiana scaffold service task          # Generate services/task_service.py
askdiana scaffold controller tasks      # Generate controllers/tasks.py
askdiana db validate                    # Check schema locally
askdiana db push --install-id <uuid> --version 1.0.0  # Register + apply schemas
askdiana package                        # Create deployment ZIP
askdiana deploy                         # Package + upload to platform
```

## Local Development

### Receiving webhooks with ngrok

```bash
python app.py           # Start your extension

ngrok http 5000         # In another terminal — creates a public HTTPS tunnel
# Use the https://xxxx.ngrok.io URL as your extension's webhook URL
```

### SSL on Windows

If you see SSL errors during local development against a self-signed instance:

```bash
ASKDIANA_VERIFY_SSL=false
```

**Do not use this in production.**

### Dynamic base URL

The Ask DIANA backend passes `askdiana_base_url` in every proxied request. The SDK
uses this to automatically resolve the correct backend URL, so your extension doesn't
need to hardcode it. This is handled transparently in `ConnectorService.register_routes()`
and `ChatService.register_routes()`.

## Authentication

| Header | Description |
|--------|-------------|
| `X-API-Key` | Your developer API key (`askd_...` format) |
| `X-Install-Id` | The install UUID (received in webhook payloads) |

**Two-layer authorization** — both layers must include the required scope:
- Your API key's scopes control what your extension *can* do
- The install's `scopes_granted` controls what the user *consented* to

## Webhook Events

| Event | Trigger | Delivered to |
|-------|---------|-------------|
| `extension.installed` | User installs your extension | `webhooks.on_install` URL |
| `extension.uninstalled` | User uninstalls your extension | `webhooks.on_uninstall` URL |
| `document.uploaded` | User uploads a document | `webhooks.on_event` URL |
| `chat.created` | User creates a new chat | `webhooks.on_event` URL |

Every webhook request includes:
- `Authorization: Bearer <ASKDIANA_API_KEY>` — verify with `verify_bearer_token()`
- `X-AskDiana-Event` — event type string

## Permission Scopes

| Scope | Description |
|-------|-------------|
| `documents:read` | List, search, and read documents |
| `documents:write` | Upload and delete documents |
| `chats:read` | List chats and read messages |
| `chats:write` | Create chats and send messages |
| `user:profile` | Read user profile info |

Data Storage, Schema Management, and Install Info require no scope.

## Examples

See the `examples/` directory:

- **[webhook_echo](examples/webhook_echo/)** — Simplest extension: log every webhook event
- **[google_drive_connector](examples/google_drive_connector/)** — Full OAuth connector with file browser and sync
- **[gemini_chat](examples/gemini_chat/)** — AI chat extension using ChatService with Gemini
- **[gamma](examples/gamma/)** — Presentation generation via the Gamma.app API
- **[notes_app](examples/notes_app/)** — CRUD app with models, services, and controllers

See also the standalone connectors in `connectors/`:
- **[google_drive](connectors/google_drive/)** — Production Google Drive connector
- **[onedrive](connectors/onedrive/)** — OneDrive connector
- **[dropbox](connectors/dropbox/)** — Dropbox connector

## API Reference

### `AskDianaClient`

| Method | Scope | Description |
|--------|-------|-------------|
| `list_documents(install_id, limit, offset)` | `documents:read` | List user's documents |
| `get_document(install_id, document_id)` | `documents:read` | Get a single document |
| `search_documents(install_id, query, limit)` | `documents:read` | Semantic document search |
| `upload_document(install_id, file_content, file_name, source_type, source_reference)` | `documents:write` | Upload a document |
| `delete_document(install_id, document_id)` | `documents:write` | Delete a document |
| `list_chats(install_id, limit, offset)` | `chats:read` | List user's chats |
| `create_chat(install_id, title, message)` | `chats:write` | Create a new chat |
| `get_chat_messages(install_id, chat_id, limit, offset)` | `chats:read` | Get chat messages |
| `send_message(install_id, chat_id, message)` | `chats:write` | Send a message |
| `get_user_profile(install_id)` | `user:profile` | Get user name, email, tenant |
| `get_install_info(install_id)` | *(none)* | Get install metadata and config |
| `get_config(install_id, key=None)` | *(none)* | Get install config or a single key |
| `get_scopes(install_id)` | *(none)* | Get granted scopes for this install |
| `get_data(install_id, namespace, key)` | *(none)* | Get a stored value |
| `set_data(install_id, namespace, key, value)` | *(none)* | Store a value |
| `delete_data(install_id, namespace, key)` | *(none)* | Delete a stored value |
| `list_data(install_id, namespace)` | *(none)* | List all keys in a namespace |
| `register_schema(install_id, version, schema)` | *(none)* | Register a table schema |
| `apply_schema(install_id, table_name)` | *(none)* | Create/update a table |

### `verify_bearer_token(authorization_header, expected_key)`

Verifies the Bearer token on incoming webhook requests. Raises `WebhookVerificationError` on failure.

```python
from askdiana import verify_bearer_token, WebhookVerificationError

try:
    verify_bearer_token(
        authorization_header=request.headers.get("Authorization", ""),
        expected_key=os.environ["ASKDIANA_API_KEY"],
    )
except WebhookVerificationError:
    return jsonify({"error": "Unauthorized"}), 401
```
