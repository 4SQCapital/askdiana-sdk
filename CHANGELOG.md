# Changelog

All notable changes to the Ask DIANA Extension SDK are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — 2026-05-01

### Added

- **`ChatService`** base class for building AI chat extensions. Subclass and implement `respond()` to handle user messages. Includes `store_conversation()`, `get_api_key()`, and `get_config()` helpers.
- **`ConnectorService`** base class for OAuth-based file sync extensions. Provides OAuth flow helpers (`store_tokens`, `get_tokens`, `clear_tokens`), a `sync_file()` workflow with cancellation and progress reporting, and `register_routes()` to wire up all API endpoints automatically.
- **`ExtensionApp`** Flask wrapper with auto-discovery of `ExtModel` subclasses in `models/` and Flask Blueprints in `controllers/`.
- **`ExtensionService`** base class for general-purpose business logic services with access to `AskDianaClient`.
- **`ExtModel` / field classes** — declarative schema system for extension database tables. Supports inheritance so child models add columns to parent tables. Fields: `StringField`, `TextField`, `IntegerField`, `FloatField`, `BooleanField`, `DateTimeField`, `DateField`, `JsonField`.
- **`register_all_models()`** — batch-register multiple `ExtModel` subclasses in a single API call.
- **CLI** — `askdiana init`, `askdiana scaffold model/service/controller`, `askdiana dev` commands.
- **Examples**: `webhook_echo`, `document_notifier`, `analytics_dashboard`, `google_drive_connector`, `data_storage`, `task_manager`, `gamma`, `gemini_chat`, `sar_workflow`.
- **`AskDianaClient`** methods: `list_documents`, `get_document`, `search_documents`, `upload_document`, `delete_document`, `list_chats`, `create_chat`, `get_chat_messages`, `send_message`, `get_user_profile`, `get_install_info`, `get_config`, `get_scopes`, `get_data`, `set_data`, `delete_data`, `list_data`, `register_schema`, `apply_schema`.

### Changed

- Bearer token authentication replaces HMAC signing. `verify_webhook()` is now a deprecated alias that raises `DeprecationWarning` at runtime. Use `verify_bearer_token()` instead.
- Sync cancellation is now signalled via `{"cancelled": true}` in the response body (HTTP 200) rather than a 409 status code.

### Fixed

- `AskDianaClient._request()` now raises a descriptive `RuntimeError` instead of a bare `JSONDecodeError` when the server returns a non-JSON response (e.g. a gateway error page).
- `ConnectorService.get_tokens()` and `clear_tokens()` now log failures at `DEBUG` level instead of silently swallowing them.
- Duplicate `__tablename__` declarations across `ExtModel` subclasses now raise `ValueError` at class definition time.

---
