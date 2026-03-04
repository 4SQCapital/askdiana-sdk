"""
Base class for building file connector extensions.

Connectors sync files from external sources (Google Drive, OneDrive,
Dropbox, S3, etc.) into Ask DIANA.  ``ConnectorService`` provides
common patterns: tracking sync history, downloading and uploading
files, and reading user config.

Usage::

    from askdiana import ConnectorService

    class GoogleDriveService(ConnectorService):
        source_type = "google_drive"

        def list_files(self, install_id, folder_id=None, page_token=None):
            api_key = self.get_config_value(install_id, "google_api_key")
            # ... call Google Drive API ...
            return files

        def download_file(self, file_id, **kwargs):
            # ... download from Google Drive ...
            return content, file_name, mime_type

    svc = GoogleDriveService(client)
    result = svc.sync_file(install_id, file_id="gdrive_abc123")
"""

import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import AskDianaClient

logger = logging.getLogger(__name__)


class ConnectorService:
    """Base class for file connector extensions.

    Subclass this and implement :meth:`download_file`.  Optionally
    override :meth:`list_files` for browsing.

    Attributes:
        source_type: Identifier for the external source (e.g.
            ``"google_drive"``).  Used when uploading documents to
            Ask DIANA.
        sync_namespace: KV namespace for storing sync history
            (default ``"sync_history"``).
    """

    source_type: str = "extension"
    sync_namespace: str = "sync_history"
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
            # 1. Download
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
