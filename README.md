# Ask DIANA Extension SDK

Python SDK for building extensions that integrate with [Ask DIANA](https://askdiana.ai).

## Installation

```bash
# From the SDK directory
pip install -e .

# Or install dependencies directly
pip install requests
```

## Quick Start

### 1. Set up webhook handling

```python
from flask import Flask, request, jsonify
from askdiana import verify_webhook, WebhookVerificationError

app = Flask(__name__)
WEBHOOK_SECRET = "your-webhook-signing-secret"

@app.route("/webhooks", methods=["POST"])
def handle_webhook():
    # Verify the request is from Ask DIANA
    try:
        verify_webhook(
            request_body=request.get_data(),
            signature_header=request.headers.get("X-AskDiana-Signature", ""),
            secret=WEBHOOK_SECRET,
            timestamp_header=request.headers.get("X-AskDiana-Delivery-Timestamp"),
        )
    except WebhookVerificationError as e:
        return jsonify({"error": str(e)}), 401

    # Process the event
    event = request.headers.get("X-AskDiana-Event")
    body = request.get_json()
    print(f"Event: {event}, Data: {body['data']}")

    return jsonify({"ok": True}), 200
```

### 2. Call the Extension API

```python
from askdiana import AskDianaClient

client = AskDianaClient(
    api_key="askd_your_api_key_here",
    base_url="https://app.askdiana.ai",
)

# Use the install_id from the webhook payload
install_id = "uuid-from-webhook-payload"

# List user's documents (requires documents:read scope)
docs = client.list_documents(install_id)
for doc in docs["documents"]:
    print(f"{doc['file_name']} ({doc['file_size']} bytes)")

# List user's chats (requires chats:read scope)
chats = client.list_chats(install_id)

# Get user profile (requires user:profile scope)
profile = client.get_user_profile(install_id)
print(f"User: {profile['user']['name']}")

# Get install metadata (no scope required)
install = client.get_install_info(install_id)
print(f"Scopes: {install['install']['scopes_granted']}")

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

### 3. Store and retrieve data

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

### 4. Define custom database tables

For extensions that need dedicated tables (beyond key-value storage), use
the declarative model syntax:

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

To register multiple models at once:

```python
from askdiana import register_all_models

register_all_models(client, install_id, "1.0.0",
                    SyncHistory, UserSettings, Accounts)
```

### 5. Model inheritance — extend tables with new fields

Models support Python inheritance. A child class inherits all parent fields
and can add new ones:

```python
from askdiana import ExtModel, StringField, IntegerField, BooleanField, DateTimeField, TextField

class TaskTracker(ExtModel):
    __tablename__ = "ext_myext_tasks"

    id = StringField(primary_key=True, max_length=36)
    install_id = StringField(max_length=36, nullable=False)
    title = StringField(max_length=500, nullable=False)
    created_at = DateTimeField(nullable=True)

class CompletableTask(TaskTracker):
    """Extends TaskTracker — inherits id, install_id, title, created_at."""
    __tablename__ = "ext_myext_tasks"  # same table

    description = TextField(nullable=True)
    priority = IntegerField(nullable=True)
    completed = BooleanField(nullable=True)

# CompletableTask.to_schema() includes ALL 7 columns
CompletableTask.setup(client, install_id, version="1.0.0")
```

### 6. Structured extension layout (recommended for larger extensions)

For extensions beyond a single file, use `ExtensionApp` with auto-discovery:

```bash
pip install askdiana[app]   # includes Flask
askdiana init my_extension  # scaffolds project structure
```

This creates:

```
my_extension/
├── app.py              # ExtensionApp entry point
├── manifest.json
├── models/             # ExtModel subclasses (auto-discovered)
│   └── task.py
├── services/           # Business logic (ExtensionService subclasses)
│   └── task_service.py
├── controllers/        # Flask Blueprints (auto-discovered)
│   └── tasks.py
└── views/              # Future: UI templates
```

**app.py:**

```python
from askdiana import ExtensionApp

app = ExtensionApp(__name__)

if __name__ == "__main__":
    app.run(port=5000)
```

`ExtensionApp` automatically:
- Creates an `AskDianaClient` from `ASKDIANA_API_KEY` env var
- Discovers ExtModel subclasses in `models/`
- Discovers and registers Flask Blueprints in `controllers/`
- Adds a `/health` endpoint

**Services** extend `ExtensionService` for business logic:

```python
from askdiana import ExtensionService

class TaskService(ExtensionService):
    def create_task(self, install_id, title):
        self.client.set_data(install_id, "tasks", title, {"title": title})
```

**Controllers** use decorators for common patterns:

```python
from flask import Blueprint, g, jsonify
from askdiana.controller import webhook_required, install_id_required

tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.route("/api/tasks", methods=["GET"])
@install_id_required
def list_tasks():
    # g.install_id is automatically extracted
    return jsonify({"tasks": []}), 200
```

**CLI scaffolding:**

```bash
askdiana init my_extension              # Create full project
askdiana scaffold model TaskTracker     # Generate models/task_tracker.py
askdiana scaffold service task          # Generate services/task_service.py
askdiana scaffold controller tasks      # Generate controllers/tasks.py
```

## Authentication

Extensions authenticate with two headers:

| Header | Description |
|--------|-------------|
| `X-API-Key` | Your developer API key (`askd_...` format) |
| `X-Install-Id` | The install UUID (received in webhook payloads) |

**Two-layer authorization:**
- Your API key's scopes control what your extension *can* do
- The install's `scopes_granted` controls what the user *consented* to

Both must include the required scope for the request to succeed.

## Webhook Events

| Event | Trigger | Webhook URL |
|-------|---------|-------------|
| `extension.installed` | User installs your extension | `webhooks.on_install` |
| `extension.uninstalled` | User uninstalls your extension | `webhooks.on_uninstall` |
| `document.uploaded` | User uploads a document | `webhooks.on_event` |
| `chat.created` | User creates a new chat | `webhooks.on_event` |

Every webhook includes:
- `X-AskDiana-Signature`: HMAC-SHA256 signature (`sha256=<hex>`)
- `X-AskDiana-Event`: Event type string
- `X-AskDiana-Delivery-Timestamp`: Unix epoch seconds

## Permission Scopes

| Scope | Description |
|-------|-------------|
| `documents:read` | List and read documents |
| `documents:write` | Create and modify documents |
| `chats:read` | List and read chats |
| `chats:write` | Create and modify chats |
| `user:profile` | Read user profile info |
| `analytics:read` | Read analytics data |

## Examples

See the `examples/` directory:

- **[webhook_echo](examples/webhook_echo/)** — Simplest extension: log every webhook event
- **[document_notifier](examples/document_notifier/)** — React to document uploads, fetch metadata via API
- **[analytics_dashboard](examples/analytics_dashboard/)** — On install, fetch user data and serve a summary dashboard
- **[google_drive_connector](examples/google_drive_connector/)** — Full cloud storage connector: OAuth, file browser, sync to Ask DIANA
- **[data_storage](examples/data_storage/)** — Key-value data storage and custom table definitions with ExtModel
- **[task_manager](examples/task_manager/)** — Structured layout: models with inheritance, services, controllers, auto-discovery

## API Reference

### `AskDianaClient(api_key, base_url, timeout)`

| Method | Scope Required | Description |
|--------|---------------|-------------|
| `list_documents(install_id, limit, offset)` | `documents:read` | List user's documents |
| `list_chats(install_id, limit, offset)` | `chats:read` | List user's chats |
| `get_user_profile(install_id)` | `user:profile` | Get user name, email, tenant |
| `get_install_info(install_id)` | *(none)* | Get install metadata |
| `upload_document(install_id, file_content, file_name, source_type, source_reference)` | `documents:write` | Upload a document on behalf of user |
| `get_data(install_id, namespace, key)` | *(none)* | Get a stored value |
| `set_data(install_id, namespace, key, value)` | *(none)* | Store a value (create or update) |
| `delete_data(install_id, namespace, key)` | *(none)* | Delete a stored value |
| `list_data(install_id, namespace)` | *(none)* | List all keys in a namespace |
| `register_schema(install_id, version, schema)` | *(none)* | Register a table schema declaration |
| `apply_schema(install_id, table_name)` | *(none)* | Create/update a registered table |

### `verify_webhook(request_body, signature_header, secret, ...)`

Verifies HMAC-SHA256 signature. Raises `WebhookVerificationError` on failure.

| Parameter | Description |
|-----------|-------------|
| `request_body` | Raw request body (bytes or str) |
| `signature_header` | `X-AskDiana-Signature` header value |
| `secret` | Your `WEBHOOK_SIGNING_SECRET` |
| `tolerance_seconds` | Max webhook age (default: 300s, set `None` to disable) |
| `timestamp_header` | `X-AskDiana-Delivery-Timestamp` header value |
