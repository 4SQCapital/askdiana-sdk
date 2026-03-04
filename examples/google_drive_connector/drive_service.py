"""
Google Drive connector service using the Ask DIANA SDK.

Extends ``ConnectorService`` to provide Google Drive file listing
and syncing via a server-side API key.
"""

import os
from typing import Any, Dict, Optional, Tuple

from askdiana import ConnectorService

import google_drive

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")


class GoogleDriveService(ConnectorService):
    """Connector service for Google Drive.

    Uses a server-side Google API key to access Drive files.
    Users configure an optional ``root_folder_id`` in the extension
    settings form.
    """

    source_type = "google_drive"

    def __init__(self, client, api_key: Optional[str] = None):
        super().__init__(client)
        self.api_key = api_key or GOOGLE_API_KEY
        if not self.api_key:
            import logging
            logging.getLogger(__name__).warning(
                "GOOGLE_API_KEY not set — file listing and sync will fail"
            )

    def list_files(
        self,
        install_id: str,
        folder_id: Optional[str] = None,
        page_token: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """List files from Google Drive.

        If no ``folder_id`` is provided, falls back to the user's
        configured ``root_folder_id``.
        """
        if not folder_id:
            folder_id = self.get_config_value(install_id, "root_folder_id") or None

        files_data = google_drive.list_files(
            api_key=self.api_key,
            folder_id=folder_id,
            page_token=page_token,
        )

        files = []
        for f in files_data.get("files", []):
            is_folder = f.get("mimeType") == "application/vnd.google-apps.folder"
            files.append({
                "id": f["id"],
                "name": f["name"],
                "mimeType": f.get("mimeType"),
                "size": int(f.get("size", 0)) if not is_folder else None,
                "modifiedTime": f.get("modifiedTime"),
                "isFolder": is_folder,
            })

        return {
            "files": files,
            "nextPageToken": files_data.get("nextPageToken"),
        }

    def download_file(
        self,
        file_id: str,
        **kwargs: Any,
    ) -> Tuple[bytes, str, str]:
        """Download a file from Google Drive."""
        return google_drive.download_file(self.api_key, file_id)
