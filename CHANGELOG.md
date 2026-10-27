# Changelog

All notable changes to the Ask DIANA Extension SDK are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added

- **User and persona context** — Ask DIANA now tells an extension who is using it and in which persona, signed with the extension's API key. Python: `verify_context()`, `request_context()` / `ExtensionApp.request_context()` (reads `X-AskDiana-Context` or the chat body's `context`; a forged one becomes a 401), and `AskDianaClient.with_context(ctx)` so document reads and search run under that user's persona. askdiana-ui: `bridge.fetch` (sends the header), `bridge.user()`, `bridge.onContext()`, and `InitData.context`. Needs a platform with `/api/extensions/<install_id>/context`; on older platforms there is no context and everything works as before.

- **`bridge.sendToChat(text)`** (askdiana-ui) — from the side panel, sends a prompt into the user's AskDiana chat in the extension's chat mode, as if they typed it (for example "Provide full details and analysis of case A-1057" when a row is opened). Resolves `"sent"`, `"busy"`, `"other_chat"` (a conversation in another mode is open), `"unavailable"`, `"no_chat"`, `"empty"`, or `"unsupported"` on a platform without the matching change.

- **`bridge.openModal(request)`** (askdiana-ui) — asks Ask DIANA to open a dialog over the whole app with the extension's `?view=modal` (`init.params` = `request`). Works from the side panel and, on platforms with the matching change, from chat response views. Resolves `false` when the host doesn't confirm, so the view can fall back to its own dialog.

### Fixed

- **`askdiana dev` picks a free port** when the port from `PORT` (or 5000) is already taken (for example by another extension in dev), registers that port, and says so. The relay finds the extension by its API key, so several extensions can run in dev at once. An explicit `--port` or a tunnel `webhook_url` is left as is.

- **`bridge.autoResize()`** (askdiana-ui) sets `#root` to `display: flow-root` while active, so the first and last child's margins are inside the measured height. Before, a short text reply could get a frame a few lines too short.

- **`applyTheme()`** (askdiana-ui) now also sets `.light` when the host is light. Before, `theme.css`'s `prefers-color-scheme: dark` fallback applied whenever `.light` was missing, so views inside a light Ask DIANA rendered with dark colours on computers set to dark mode.

### Added

- **`AskDianaClient.search_documents()`** — `POST /api/ext/documents/search`: the platform's hybrid search (dense + BM25) over the documents the installing user can read, optionally narrowed to one project or team and/or a list of document IDs. Returns matching chunks with `document_id`, `file_name`, `section`, `page` and `score`. Needs a platform with that route; older platforms answer 404 or 405.

---

## [0.2.0] — 2026-09-25

### Added

- **`askdiana.erp` connector kit** — build ERP/CRM connector extensions from a YAML pack. `ErpExtension(pack_path, demo_provider=...).mount(app)` registers auth, chat, dashboard and data routes. Supports `oauth2`, `token`, `basic` and `session` logins, paging, caching, retries, and any OpenAI-compatible or Anthropic LLM (`LLM_*` env vars; legacy `GENIUS2_*` still read).
- `pyyaml>=6.0` added to the `app` extra.
- `tests/erp/` — unit tests for the kit.
- **Custom chat response views** — declaring `"response": true` under `ui.views` in `manifest.json` makes the platform render the extension's own `views/response.tsx` inline in the chat message (iframe at `ui.url?view=response`) instead of the host-rendered `rich_response` blocks. After `ready`, the host `init` carries `params: { blocks, content, message_id }`. Falls back to host rendering if the view fails to load.
- **`bridge.autoResize()`** (askdiana-ui) — keeps the host iframe sized to the document via a `ResizeObserver` posting `resize` messages; returns a disconnect function. The `askdiana init` scaffold's `views/index.tsx` now calls it for the response view.
- Scaffold manifest now declares `"response": true`; scaffold `views/response.tsx` renders `init.params.blocks` / `init.params.content` before its hand-authored fallback.
- `examples/notes_app` and `examples/analytics_dashboard` updated to demonstrate the response view end-to-end.

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
- **`AskDianaClient`** methods: `list_documents`, `get_document`, `get_document_content`, `list_project_documents`, `list_team_documents`, `upload_document`, `delete_document`, `list_chats`, `create_chat`, `get_chat_messages`, `send_message`, `get_user_profile`, `get_install_info`, `get_config`, `get_scopes`, `get_data`, `set_data`, `delete_data`, `list_data`, `register_schema`, `apply_schema`.

### Changed

- Bearer token authentication replaces HMAC signing. `verify_webhook()` is now a deprecated alias that raises `DeprecationWarning` at runtime. Use `verify_bearer_token()` instead.
- Sync cancellation is now signalled via `{"cancelled": true}` in the response body (HTTP 200) rather than a 409 status code.

### Fixed

- `AskDianaClient._request()` now raises a descriptive `RuntimeError` instead of a bare `JSONDecodeError` when the server returns a non-JSON response (e.g. a gateway error page).
- `ConnectorService.get_tokens()` and `clear_tokens()` now log failures at `DEBUG` level instead of silently swallowing them.
- Duplicate `__tablename__` declarations across `ExtModel` subclasses now raise `ValueError` at class definition time.

---
