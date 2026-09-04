"""
API client for the Ask DIANA Extension API (``/api/ext``).

Extensions use this client to read data from Ask DIANA on behalf of the
users who installed them.

Usage::

    from askdiana import AskDianaClient

    client = AskDianaClient(api_key="askd_xxxxx")

    # Use the install_id from the webhook payload
    docs = client.list_documents(install_id="...")
    for doc in docs["documents"]:
        print(doc["file_name"])

    # Read a document's extracted text
    content = client.get_document_content(install_id="...", document_id="...")["content"]

    # Get user config
    config = client.get_config(install_id="...", key="google_api_key")
"""

import os
import threading
import time
import requests
from typing import Optional, Dict, Any, List


# How long to cache install metadata (config, scopes) before re-fetching.
# Tunable via env so deployments with rapid config churn can shorten it.
# Cache is invalidated immediately on any 4xx response so a revoke or
# reinstall isn't stuck on stale data for the full TTL.
_INSTALL_INFO_TTL = int(os.environ.get("ASKDIANA_SDK_CACHE_TTL", "30"))


class AskDianaClient:
    """Client for the Ask DIANA Extension API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://app.askdiana.ai",
        timeout: int = 30,
        verify_ssl: bool = True,
    ):
        """
        Args:
            api_key: Your developer API key (``askd_...`` format).
            base_url: Ask DIANA instance URL (no trailing slash).
            timeout: HTTP request timeout in seconds.
            verify_ssl: If False, skip SSL cert verification (local dev).
        """
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        self._session.verify = verify_ssl
        self._session.headers.update({
            "X-API-Key": self.api_key,
        })
        # TTL cache: install_id -> (expires_at, install_info_dict)
        self._install_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
        self._install_cache_lock = threading.Lock()

    def _invalidate_install_cache(self, install_id: str) -> None:
        with self._install_cache_lock:
            self._install_cache.pop(install_id, None)

    def _request(
        self,
        method: str,
        path: str,
        install_id: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Extension API."""
        url = f"{self.base_url}/api/ext{path}"
        headers = {"X-Install-Id": install_id}
        response = self._session.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_body,
            timeout=self.timeout,
        )
        # On any 4xx (revoked key, scope change, install disabled) drop the
        # cached install snapshot so the next call hits the backend fresh
        # instead of looping on stale state.
        if 400 <= response.status_code < 500:
            self._invalidate_install_cache(install_id)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            raise RuntimeError(
                f"Non-JSON response from API ({response.status_code}): "
                f"{response.text[:200]}"
            )

    # ------------------------------------------------------------------ #
    # Endpoints                                                            #
    # ------------------------------------------------------------------ #

    def list_documents(
        self,
        install_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List documents for the installing user.

        Requires scope: ``documents:read``

        Returns::

            {
                "success": true,
                "documents": [
                    {"id": "...", "file_name": "...", "file_type": "...",
                     "file_size": 12345, "created_at": "..."}
                ]
            }
        """
        return self._request(
            "GET", "/documents", install_id,
            params={"limit": limit, "offset": offset},
        )

    def list_chats(
        self,
        install_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List chats for the installing user.

        Requires scope: ``chats:read``

        Returns::

            {
                "success": true,
                "chats": [
                    {"id": "...", "title": "...", "created_at": "..."}
                ]
            }
        """
        return self._request(
            "GET", "/chats", install_id,
            params={"limit": limit, "offset": offset},
        )

    def get_user_profile(self, install_id: str) -> Dict[str, Any]:
        """Get the installing user's profile.

        Requires scope: ``user:profile``

        Returns::

            {
                "success": true,
                "user": {"id": "...", "name": "...", "email": "...",
                         "tenant_id": "..."}
            }
        """
        return self._request("GET", "/user/profile", install_id)

    def list_projects(
        self,
        install_id: str,
    ) -> Dict[str, Any]:
        """List active projects for the install's tenant.

        Requires scope: ``projects:read``

        Returns::

            {
                "success": true,
                "projects": [
                    {"id": "...", "name": "...", "description": "...",
                     "icon": "...", "color": "..."}
                ]
            }
        """
        return self._request("GET", "/projects", install_id)

    def list_teams(
        self,
        install_id: str,
    ) -> Dict[str, Any]:
        """List teams (departments) for the install's tenant.

        Requires scope: ``teams:read``

        Returns::

            {
                "success": true,
                "teams": [
                    {"id": "...", "name": "...", "description": "..."}
                ]
            }
        """
        return self._request("GET", "/teams", install_id)

    def list_project_documents(
        self,
        install_id: str,
        project_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List documents shared into a project.

        The installing user must be a member of the project; otherwise the
        call returns 404.

        Requires scopes: ``projects:read`` and ``documents:read``

        Returns::

            {
                "success": true,
                "project": {"id": "...", "name": "..."},
                "documents": [{"id": "...", "file_name": "...", ...}]
            }
        """
        return self._request(
            "GET", f"/projects/{project_id}/documents", install_id,
            params={"limit": limit, "offset": offset},
        )

    def list_team_documents(
        self,
        install_id: str,
        team_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List documents shared with a team (department).

        The installing user must be a member of the team; otherwise the call
        returns 404.

        Requires scopes: ``teams:read`` and ``documents:read``

        Returns::

            {
                "success": true,
                "team": {"id": "...", "name": "..."},
                "documents": [{"id": "...", "file_name": "...", ...}]
            }
        """
        return self._request(
            "GET", f"/teams/{team_id}/documents", install_id,
            params={"limit": limit, "offset": offset},
        )

    def get_install_info(self, install_id: str) -> Dict[str, Any]:
        """Get install metadata (scopes, config, status).

        Cached in-process for ASKDIANA_SDK_CACHE_TTL seconds (default 30).
        Callers that read multiple config keys (``get_config(... "a")`` then
        ``get_config(... "b")``) hit the cache and avoid one round-trip per
        key. The cache is invalidated whenever any request for this install
        returns 4xx, so revokes/scope changes surface within one failed call.
        """
        with self._install_cache_lock:
            entry = self._install_cache.get(install_id)
            if entry and entry[0] > time.time():
                return entry[1]
        info = self._request("GET", "/install", install_id)
        with self._install_cache_lock:
            self._install_cache[install_id] = (time.time() + _INSTALL_INFO_TTL, info)
        return info

    def upload_document(
        self,
        install_id: str,
        file_content: bytes,
        file_name: str,
        source_type: str = "extension",
        source_reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a document on behalf of the installing user.

        Requires scope: ``documents:write``

        Args:
            install_id: Install UUID from webhook payload.
            file_content: Raw file bytes.
            file_name: Original file name (e.g. ``report.pdf``).
            source_type: Source identifier (e.g. ``google_drive``).
            source_reference: Optional reference ID in the source system.

        Returns::

            {
                "success": true,
                "document": {"id": "...", "file_name": "...", ...},
                "message": "Document accepted for processing"
            }
        """
        url = f"{self.base_url}/api/ext/documents/upload"
        headers = {"X-Install-Id": install_id}
        files = {"file": (file_name, file_content)}
        data: Dict[str, str] = {"source_type": source_type}
        if source_reference:
            data["source_reference"] = source_reference

        # Use a longer timeout for file uploads — the backend needs time
        # to receive, store, and begin processing the document.
        upload_timeout = max(self.timeout, 300)
        response = self._session.post(
            url,
            headers=headers,
            files=files,
            data=data,
            timeout=upload_timeout,
        )
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            raise RuntimeError(
                f"Non-JSON response from upload API ({response.status_code}): "
                f"{response.text[:200]}"
            )

    def get_document(
        self,
        install_id: str,
        document_id: str,
    ) -> Dict[str, Any]:
        """Get a single document by ID.

        Requires scope: ``documents:read``

        Args:
            install_id: Install UUID from webhook payload.
            document_id: The document UUID.

        Returns::

            {
                "success": true,
                "document": {"id": "...", "file_name": "...", ...}
            }
        """
        return self._request("GET", f"/documents/{document_id}", install_id)

    def get_document_content(
        self,
        install_id: str,
        document_id: str,
    ) -> Dict[str, Any]:
        """Get the extracted text of a document.

        Text is re-extracted from the original upload when it is still on disk
        (``content_source: "file"``), otherwise reassembled from the document's
        indexed chunks (``content_source: "chunks"``).

        Requires scope: ``documents:read``

        Args:
            install_id: Install UUID from webhook payload.
            document_id: The document UUID.

        Returns::

            {
                "success": true,
                "document": {"id": "...", "file_name": "...", ...},
                "content": "the extracted text...",
                "content_source": "file",
                "length": 12345
            }
        """
        return self._request("GET", f"/documents/{document_id}/content", install_id)

    def delete_document(
        self,
        install_id: str,
        document_id: str,
    ) -> Dict[str, Any]:
        """Delete a document.

        Requires scope: ``documents:write``

        Args:
            install_id: Install UUID from webhook payload.
            document_id: The document UUID to delete.

        Returns::

            {"success": true, "message": "Document deleted"}
        """
        return self._request("DELETE", f"/documents/{document_id}", install_id)

    # ------------------------------------------------------------------ #
    # Chats (extended)                                                      #
    # ------------------------------------------------------------------ #

    def create_chat(
        self,
        install_id: str,
        title: Optional[str] = None,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new chat, optionally with an initial message.

        Requires scope: ``chats:write``

        Args:
            install_id: Install UUID from webhook payload.
            title: Optional chat title.
            message: Optional initial message to send.

        Returns::

            {
                "success": true,
                "chat": {"id": "...", "title": "...", "created_at": "..."}
            }
        """
        body: Dict[str, Any] = {}
        if title:
            body["title"] = title
        if message:
            body["message"] = message
        return self._request("POST", "/chats", install_id, json_body=body)

    def get_chat_messages(
        self,
        install_id: str,
        chat_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get messages from a chat.

        Requires scope: ``chats:read``

        Args:
            install_id: Install UUID from webhook payload.
            chat_id: The chat UUID.
            limit: Maximum number of messages.
            offset: Pagination offset.

        Returns::

            {
                "success": true,
                "messages": [
                    {"id": "...", "role": "user", "content": "...",
                     "created_at": "..."}
                ]
            }
        """
        return self._request(
            "GET", f"/chats/{chat_id}/messages", install_id,
            params={"limit": limit, "offset": offset},
        )

    def send_message(
        self,
        install_id: str,
        chat_id: str,
        message: str,
    ) -> Dict[str, Any]:
        """Send a message to a chat.

        Requires scope: ``chats:write``

        Args:
            install_id: Install UUID from webhook payload.
            chat_id: The chat UUID.
            message: The message text.

        Returns::

            {
                "success": true,
                "message": {"id": "...", "content": "...", ...}
            }
        """
        return self._request(
            "POST", f"/chats/{chat_id}/messages", install_id,
            json_body={"message": message},
        )

    # ------------------------------------------------------------------ #
    # Install & Config helpers                                              #
    # ------------------------------------------------------------------ #

    def get_config(
        self,
        install_id: str,
        key: Optional[str] = None,
    ) -> Any:
        """Get the user's extension config (or a single key).

        Convenience wrapper around :meth:`get_install_info`.

        Args:
            install_id: Install UUID from webhook payload.
            key: If provided, return only this config key's value.
                 Returns ``None`` if the key doesn't exist.

        Returns:
            The full config dict, or the value for *key*.
        """
        info = self.get_install_info(install_id)
        config = info.get("install", {}).get("config", {}) or {}
        if key is not None:
            return config.get(key)
        return config

    def get_scopes(self, install_id: str) -> List[str]:
        """Get the scopes granted by the user for this install.

        Convenience wrapper around :meth:`get_install_info`.

        Returns:
            List of scope strings (e.g. ``["documents:read", "user:profile"]``).
        """
        info = self.get_install_info(install_id)
        return info.get("install", {}).get("scopes_granted", [])

    # ------------------------------------------------------------------ #
    # Extension Data Storage                                               #
    # ------------------------------------------------------------------ #

    def get_data(
        self,
        install_id: str,
        namespace: str,
        key: str,
    ) -> Dict[str, Any]:
        """Get a stored value by namespace and key.

        No specific scope required.

        Returns::

            {
                "success": true,
                "data": {"namespace": "...", "key": "...",
                         "value": ..., "updated_at": "..."}
            }

        Raises:
            requests.HTTPError: 404 if key not found.
        """
        return self._request("GET", f"/data/{namespace}/{key}", install_id)

    def set_data(
        self,
        install_id: str,
        namespace: str,
        key: str,
        value: Any,
    ) -> Dict[str, Any]:
        """Store a value under namespace/key (creates or updates).

        No specific scope required.

        Args:
            install_id: Install UUID from webhook payload.
            namespace: Data namespace (e.g. ``"settings"``).
            key: The key to store under.
            value: Any JSON-serializable value.

        Returns::

            {"success": true, "message": "Data saved"}
        """
        return self._request(
            "PUT", f"/data/{namespace}/{key}", install_id,
            json_body={"value": value},
        )

    def delete_data(
        self,
        install_id: str,
        namespace: str,
        key: str,
    ) -> Dict[str, Any]:
        """Delete a stored value by namespace and key.

        No specific scope required.

        Returns::

            {"success": true, "message": "Data deleted"}

        Raises:
            requests.HTTPError: 404 if key not found.
        """
        return self._request("DELETE", f"/data/{namespace}/{key}", install_id)

    def list_data(
        self,
        install_id: str,
        namespace: str,
    ) -> Dict[str, Any]:
        """List all keys and values in a namespace.

        No specific scope required.

        Returns::

            {
                "success": true,
                "data": [
                    {"key": "...", "value": ..., "updated_at": "..."},
                    ...
                ]
            }
        """
        return self._request("GET", f"/data/{namespace}", install_id)

    # ------------------------------------------------------------------ #
    # Extension Schema Management                                          #
    # ------------------------------------------------------------------ #

    def register_schema(
        self,
        install_id: str,
        version: str,
        schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Register a schema declaration for this extension.

        Table names must start with ``ext_``.  No specific scope required.

        Args:
            install_id: Install UUID from webhook payload.
            version: Extension version string (e.g. ``"1.0.0"``).
            schema: Schema dict::

                {"tables": [{"name": "ext_...", "columns": [...]}]}

        Returns::

            {"success": true, "message": "Schema registered",
             "schema_id": "uuid"}

        Raises:
            requests.HTTPError: 400 if schema validation fails.
        """
        return self._request(
            "POST", "/schema/register", install_id,
            json_body={"version": version, "schema": schema},
        )

    def apply_schema(
        self,
        install_id: str,
        table_name: str,
    ) -> Dict[str, Any]:
        """Apply a registered schema to create/update a table.

        Must be called after :meth:`register_schema`.

        Args:
            install_id: Install UUID from webhook payload.
            table_name: The ``ext_*`` table name to apply.

        Returns::

            {"success": true, "message": "Schema applied"}
        """
        return self._request(
            "POST", "/schema/apply", install_id,
            json_body={"table_name": table_name},
        )
