"""
Base class for building file connector extensions.

Connectors sync files from external sources (Google Drive, OneDrive,
Dropbox, S3, etc.) into Ask DIANA.  ``ConnectorService`` provides
common patterns: OAuth authentication, tracking sync history,
downloading and uploading files, and reading user config.

Usage::

    from askdiana import ConnectorService

    class GoogleDriveService(ConnectorService):
        source_type = "google_drive"
        provider_name = "google_drive"

        def get_auth_url(self, install_id, redirect_uri):
            return "https://accounts.google.com/o/oauth2/v2/auth?..."

        def handle_auth_callback(self, install_id, code, redirect_uri):
            # Exchange code for tokens, store via client.set_data()
            return {"connected": True, "account_email": "user@gmail.com"}

        def get_auth_status(self, install_id):
            return {"connected": True, "account_email": "user@gmail.com"}

        def disconnect(self, install_id):
            return {"disconnected": True}

        def list_files(self, install_id, folder_id=None, page_token=None):
            return {"files": [...], "nextPageToken": None}

        def download_file(self, file_id, **kwargs):
            return content, file_name, mime_type

    app = ExtensionApp(__name__, auto_discover=False)
    svc = GoogleDriveService(app.client)
    svc.register_routes(app)
"""

import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import AskDianaClient
    from .app import ExtensionApp

logger = logging.getLogger(__name__)


class ConnectorService:
    """Base class for file connector extensions with OAuth support.

    Subclass this and implement the OAuth methods
    (:meth:`get_auth_url`, :meth:`handle_auth_callback`,
    :meth:`get_auth_status`, :meth:`disconnect`) and the file methods
    (:meth:`list_files`, :meth:`download_file`).

    Call :meth:`register_routes` to wire up all API endpoints
    automatically on an ``ExtensionApp``.

    Attributes:
        source_type: Identifier for the external source (e.g.
            ``"google_drive"``).  Used when uploading documents to
            Ask DIANA.
        provider_name: Display name / identifier for this provider
            (e.g. ``"google_drive"``).  Returned in auth status.
        sync_namespace: KV namespace for storing sync history
            (default ``"sync_history"``).
        auth_namespace: KV namespace for storing OAuth tokens
            (default ``"oauth_tokens"``).
    """

    source_type: str = "extension"
    provider_name: str = "extension"
    sync_namespace: str = "sync_history"
    auth_namespace: str = "oauth_tokens"
    store_history: bool = False

    def __init__(self, client: "AskDianaClient", store_history: bool = False):
        """
        Args:
            client: AskDianaClient instance.
            store_history: If ``True``, sync records are stored in the
                ``ask_extensions`` database via ``client.set_data()``.
                If ``False`` (default), only the main ``ask`` database
                is used through the scopes (documents:write, etc.).
        """
        self.client = client
        self.store_history = store_history

    # ------------------------------------------------------------------ #
    # Config helpers                                                       #
    # ------------------------------------------------------------------ #

    def get_config_value(self, install_id: str, key: str) -> Any:
        """Read a single value from the user's extension config.

        Returns ``None`` if the key is not set.
        """
        return self.client.get_config(install_id, key)

    def require_config_value(self, install_id: str, key: str) -> Any:
        """Read a config value, raising ``ValueError`` if missing."""
        value = self.get_config_value(install_id, key)
        if not value:
            raise ValueError(
                f"Missing required config '{key}'. "
                "Update extension settings."
            )
        return value

    # ------------------------------------------------------------------ #
    # OAuth operations (override in subclass)                              #
    # ------------------------------------------------------------------ #

    def get_auth_url(self, install_id: str, redirect_uri: str) -> str:
        """Return the OAuth authorization URL for this provider.

        Override in your subclass.

        Args:
            install_id: Install UUID from the webhook payload.
            redirect_uri: URL to redirect to after authorization.

        Returns:
            The full OAuth authorization URL.
        """
        raise NotImplementedError("Subclass must implement get_auth_url()")

    def handle_auth_callback(
        self, install_id: str, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange the OAuth authorization code for tokens.

        Override in your subclass.  Should store tokens via
        ``client.set_data()`` and return account info.

        Args:
            install_id: Install UUID.
            code: The OAuth authorization code.
            redirect_uri: The redirect URI used in the original request.

        Returns:
            Dict with ``"connected"`` bool, ``"account_email"`` str, etc.
        """
        raise NotImplementedError("Subclass must implement handle_auth_callback()")

    def get_auth_status(self, install_id: str) -> Dict[str, Any]:
        """Return the current OAuth connection status.

        Override in your subclass.

        Returns:
            Dict with ``"connected"`` bool, ``"account_email"`` str or None,
            and ``"provider"`` str.
        """
        raise NotImplementedError("Subclass must implement get_auth_status()")

    def disconnect(self, install_id: str) -> Dict[str, Any]:
        """Revoke OAuth tokens and clear stored credentials.

        Override in your subclass.

        Returns:
            Dict with ``"disconnected"`` bool.
        """
        raise NotImplementedError("Subclass must implement disconnect()")

    # ------------------------------------------------------------------ #
    # Token storage helpers                                                #
    # ------------------------------------------------------------------ #

    def store_tokens(self, install_id: str, tokens: Dict[str, Any]) -> None:
        """Store OAuth tokens in the extension data store."""
        self.client.set_data(install_id, self.auth_namespace, "tokens", tokens)

    def get_tokens(self, install_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored OAuth tokens, or None if not found."""
        try:
            result = self.client.get_data(install_id, self.auth_namespace, "tokens")
            return result.get("data", {}).get("value")
        except Exception:
            return None

    def clear_tokens(self, install_id: str) -> None:
        """Delete stored OAuth tokens."""
        try:
            self.client.delete_data(install_id, self.auth_namespace, "tokens")
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Route registration                                                   #
    # ------------------------------------------------------------------ #

    def register_routes(self, ext_app: "ExtensionApp", verify_signature: bool = True) -> None:
        """Register all connector API routes on the ExtensionApp.

        Wires up:
        - ``GET  /api/auth/status``   → :meth:`get_auth_status`
        - ``GET  /api/auth/url``      → :meth:`get_auth_url`
        - ``POST /api/auth/callback`` → :meth:`handle_auth_callback`
        - ``POST /api/auth/disconnect`` → :meth:`disconnect`
        - ``GET  /api/files``         → :meth:`list_files`
        - ``POST /api/sync``          → :meth:`sync_file`

        Args:
            ext_app: The ExtensionApp instance.
            verify_signature: If True, verify ``X-AskDiana-Signature``
                on all connector routes.  Ensures only the Ask backend
                (or other trusted callers) can invoke these endpoints.
                Set to ``False`` for local development.
        """
        from flask import request as flask_request, jsonify as flask_jsonify
        from functools import wraps

        svc = self
        _ext_app = ext_app

        def _require_signature(f):
            """Decorator that verifies webhook signature on connector routes.

            For POST requests, verifies against the raw body.
            For GET requests, verifies against a JSON-serialized dict
            of query parameters (matching the proxy's signing approach).
            """
            @wraps(f)
            def wrapper(*args, **kwargs):
                if not verify_signature:
                    return f(*args, **kwargs)
                if not _ext_app._webhook_secret:
                    # No secret configured — skip verification
                    return f(*args, **kwargs)
                try:
                    import json as _json
                    from .webhooks import verify_webhook, WebhookVerificationError
                    if flask_request.method == "GET":
                        # For GET, the proxy signed json.dumps(params, sort_keys=True)
                        params = dict(flask_request.args)
                        body = _json.dumps(params, sort_keys=True, default=str)
                    else:
                        body = flask_request.get_data()
                    verify_webhook(
                        request_body=body,
                        signature_header=flask_request.headers.get("X-AskDiana-Signature", ""),
                        secret=_ext_app._webhook_secret,
                        timestamp_header=flask_request.headers.get("X-AskDiana-Delivery-Timestamp"),
                    )
                except WebhookVerificationError as exc:
                    logger.warning("Connector route signature verification failed: %s", exc)
                    return flask_jsonify({"error": "Unauthorized"}), 401
                return f(*args, **kwargs)
            return wrapper

        @ext_app.flask.route("/api/auth/status", methods=["GET"])
        @_require_signature
        def _auth_status():
            install_id = flask_request.args.get("install_id")
            if not install_id:
                return flask_jsonify({"error": "install_id required"}), 400
            try:
                result = svc.get_auth_status(install_id)
                result["provider"] = svc.provider_name
                return flask_jsonify({"success": True, **result}), 200
            except Exception as e:
                logger.error("Auth status error: %s", e, exc_info=True)
                return flask_jsonify({"error": str(e)}), 500

        @ext_app.flask.route("/api/auth/url", methods=["GET"])
        @_require_signature
        def _auth_url():
            install_id = flask_request.args.get("install_id")
            redirect_uri = flask_request.args.get("redirect_uri", "")
            if not install_id:
                return flask_jsonify({"error": "install_id required"}), 400
            try:
                url = svc.get_auth_url(install_id, redirect_uri)
                return flask_jsonify({"success": True, "auth_url": url}), 200
            except Exception as e:
                logger.error("Auth URL error: %s", e, exc_info=True)
                return flask_jsonify({"error": str(e)}), 500

        @ext_app.flask.route("/api/auth/callback", methods=["POST"])
        @_require_signature
        def _auth_callback():
            data = flask_request.get_json() or {}
            install_id = data.get("install_id")
            code = data.get("code")
            redirect_uri = data.get("redirect_uri", "")
            if not install_id or not code:
                return flask_jsonify({"error": "install_id and code required"}), 400
            try:
                result = svc.handle_auth_callback(install_id, code, redirect_uri)
                return flask_jsonify({"success": True, **result}), 200
            except Exception as e:
                logger.error("Auth callback error: %s", e, exc_info=True)
                return flask_jsonify({"error": str(e)}), 500

        @ext_app.flask.route("/api/auth/disconnect", methods=["POST"])
        @_require_signature
        def _auth_disconnect():
            data = flask_request.get_json() or {}
            install_id = data.get("install_id")
            if not install_id:
                return flask_jsonify({"error": "install_id required"}), 400
            try:
                result = svc.disconnect(install_id)
                return flask_jsonify({"success": True, **result}), 200
            except Exception as e:
                logger.error("Disconnect error: %s", e, exc_info=True)
                return flask_jsonify({"error": str(e)}), 500

        @ext_app.flask.route("/api/files", methods=["GET"])
        @_require_signature
        def _list_files():
            install_id = flask_request.args.get("install_id")
            if not install_id:
                return flask_jsonify({"error": "install_id required"}), 400
            try:
                result = svc.list_files(
                    install_id=install_id,
                    folder_id=flask_request.args.get("folder_id"),
                    page_token=flask_request.args.get("page_token"),
                )
                return flask_jsonify({"success": True, **result}), 200
            except Exception as e:
                logger.error("List files error: %s", e, exc_info=True)
                return flask_jsonify({"error": str(e)}), 500

        @ext_app.flask.route("/api/sync", methods=["POST"])
        @_require_signature
        def _sync_file():
            data = flask_request.get_json() or {}
            install_id = data.get("install_id")
            file_id = data.get("file_id")
            if not install_id or not file_id:
                return flask_jsonify({"error": "install_id and file_id required"}), 400
            try:
                result = svc.sync_file(install_id=install_id, file_id=file_id)
                return flask_jsonify(result), 200
            except Exception as e:
                logger.error("Sync error: %s", e, exc_info=True)
                return flask_jsonify({"error": str(e)}), 500

    # ------------------------------------------------------------------ #
    # File operations (override in subclass)                               #
    # ------------------------------------------------------------------ #

    def list_files(
        self,
        install_id: str,
        folder_id: Optional[str] = None,
        page_token: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """List files from the external source.

        Override in your subclass.

        Returns:
            Dict with ``"files"`` list and optional ``"nextPageToken"``.
        """
        raise NotImplementedError("Subclass must implement list_files()")

    def download_file(
        self,
        file_id: str,
        **kwargs: Any,
    ) -> Tuple[bytes, str, str]:
        """Download a file from the external source.

        Override in your subclass.

        Args:
            file_id: The file identifier in the external system.

        Returns:
            Tuple of ``(content_bytes, file_name, mime_type)``.
        """
        raise NotImplementedError("Subclass must implement download_file()")

    # ------------------------------------------------------------------ #
    # Sync workflow                                                        #
    # ------------------------------------------------------------------ #

    def sync_file(
        self,
        install_id: str,
        file_id: str,
        **download_kwargs: Any,
    ) -> Dict[str, Any]:
        """Download a file from the external source and upload to Ask DIANA.

        This is the main sync workflow:

        1. Download from external source via :meth:`download_file`
        2. Upload to Ask DIANA via ``client.upload_document``
           (stored in the main ``ask`` database)
        3. Optionally record sync history in ``ask_extensions`` DB
           (only when ``store_history=True``)

        Args:
            install_id: Install UUID from webhook payload.
            file_id: File identifier in the external source.
            **download_kwargs: Extra kwargs passed to :meth:`download_file`.

        Returns:
            Dict with ``"success"``, ``"file_name"``, and ``"document"``
            keys.
        """
        file_name = file_id
        try:
            # 1. Download — pass install_id so subclasses can use it
            download_kwargs.setdefault("install_id", install_id)
            content, file_name, mime_type = self.download_file(
                file_id, **download_kwargs
            )
            logger.info(
                "Downloaded: %s (%d bytes, %s)",
                file_name, len(content), mime_type,
            )

            # 2. Upload to Ask DIANA
            result = self.client.upload_document(
                install_id=install_id,
                file_content=content,
                file_name=file_name,
                source_type=self.source_type,
                source_reference=file_id,
            )

            # 3. Record in ask_extensions DB (only if store_history enabled)
            if self.store_history:
                doc_id = (
                    result.get("document", {}).get("id")
                    if result.get("success") else None
                )
                self._record_sync(
                    install_id=install_id,
                    file_id=file_id,
                    file_name=file_name,
                    document_id=doc_id,
                    status="success",
                )

            return {
                "success": True,
                "file_name": file_name,
                "document": result.get("document"),
            }

        except Exception as exc:
            logger.error("Sync error for %s: %s", file_id, exc, exc_info=True)
            if self.store_history:
                self._record_sync(
                    install_id=install_id,
                    file_id=file_id,
                    file_name=file_name,
                    document_id=None,
                    status="error",
                    error_message=str(exc),
                )
            raise

    def get_sync_history(
        self,
        install_id: str,
    ) -> List[Dict[str, Any]]:
        """Get sync history for an install, newest first.

        Returns:
            List of sync records (dicts with ``file_name``, ``status``,
            ``synced_at``, etc.).
        """
        result = self.client.list_data(install_id, self.sync_namespace)
        items = result.get("data", [])
        records = [item.get("value", {}) for item in items if item.get("value")]
        records.sort(
            key=lambda r: r.get("synced_at", ""),
            reverse=True,
        )
        return records

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _record_sync(
        self,
        install_id: str,
        file_id: str,
        file_name: str,
        document_id: Optional[str],
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Store a sync record in the extensions KV store."""
        sync_id = str(uuid.uuid4())
        record: Dict[str, Any] = {
            "source_file_id": file_id,
            "file_name": file_name,
            "askdiana_document_id": document_id,
            "status": status,
            "synced_at": datetime.utcnow().isoformat(),
        }
        if error_message:
            record["error_message"] = error_message
        try:
            self.client.set_data(install_id, self.sync_namespace, sync_id, record)
        except Exception as exc:
            logger.warning("Failed to record sync: %s", exc)
