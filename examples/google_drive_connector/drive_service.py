"""
Google Drive connector service using the Ask DIANA SDK.

Extends ``ConnectorService`` to provide Google Drive file listing
and syncing via OAuth2 (user authorizes their Google account).
"""

import os
import logging
import time
from typing import Any, Dict, Optional, Tuple

from askdiana import ConnectorService

import google_drive

logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")


class GoogleDriveService(ConnectorService):
    """Connector service for Google Drive with OAuth.

    Users connect their Google account via OAuth. Tokens are stored
    in the Ask DIANA extension data store (ask_extensions DB).
    """

    source_type = "google_drive"
    provider_name = "google_drive"

    def __init__(self, client, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        super().__init__(client)
        self.client_id = client_id or GOOGLE_CLIENT_ID
        self.client_secret = client_secret or GOOGLE_CLIENT_SECRET
        if not self.client_id or not self.client_secret:
            logger.warning(
                "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not set — OAuth will fail"
            )

    # ------------------------------------------------------------------ #
    # OAuth implementation                                                 #
    # ------------------------------------------------------------------ #

    def get_auth_url(self, install_id: str, redirect_uri: str) -> str:
        """Build Google OAuth URL with install_id as state."""
        return google_drive.build_auth_url(
            client_id=self.client_id,
            redirect_uri=redirect_uri,
            state=install_id,
        )

    def handle_auth_callback(
        self, install_id: str, code: str, redirect_uri: str
    ) -> Dict[str, Any]:
        """Exchange code for tokens, store them, return account info."""
        token_data = google_drive.exchange_code(
            code=code,
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=redirect_uri,
        )

        access_token = token_data["access_token"]
        user_info = google_drive.get_user_info(access_token)

        # Store tokens in extension data store
        self.store_tokens(install_id, {
            "access_token": access_token,
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": time.time() + token_data.get("expires_in", 3600),
            "account_email": user_info.get("email"),
        })

        return {
            "connected": True,
            "account_email": user_info.get("email"),
        }

    def get_auth_status(self, install_id: str) -> Dict[str, Any]:
        """Check if we have valid tokens for this install."""
        tokens = self.get_tokens(install_id)
        if not tokens or not tokens.get("access_token"):
            return {"connected": False, "account_email": None}
        return {
            "connected": True,
            "account_email": tokens.get("account_email"),
        }

    def disconnect(self, install_id: str) -> Dict[str, Any]:
        """Revoke Google tokens and clear stored credentials."""
        tokens = self.get_tokens(install_id)
        if tokens:
            # Try revoking with Google
            token = tokens.get("refresh_token") or tokens.get("access_token")
            if token:
                google_drive.revoke_token(token)
        self.clear_tokens(install_id)
        return {"disconnected": True}

    # ------------------------------------------------------------------ #
    # Token management                                                     #
    # ------------------------------------------------------------------ #

    def _get_valid_access_token(self, install_id: str) -> str:
        """Get a valid access token, refreshing if expired."""
        tokens = self.get_tokens(install_id)
        if not tokens:
            raise ValueError("Not connected to Google Drive. Please authorize first.")

        # Check if token is expired (with 60s buffer)
        if tokens.get("expires_at", 0) < time.time() + 60:
            refresh_token = tokens.get("refresh_token")
            if not refresh_token:
                raise ValueError("Token expired and no refresh token available. Please re-authorize.")

            new_token_data = google_drive.refresh_access_token(
                refresh_token=refresh_token,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            tokens["access_token"] = new_token_data["access_token"]
            tokens["expires_at"] = time.time() + new_token_data.get("expires_in", 3600)
            if "refresh_token" in new_token_data:
                tokens["refresh_token"] = new_token_data["refresh_token"]
            self.store_tokens(install_id, tokens)

        return tokens["access_token"]

    # ------------------------------------------------------------------ #
    # File operations                                                      #
    # ------------------------------------------------------------------ #

    def list_files(
        self,
        install_id: str,
        folder_id: Optional[str] = None,
        page_token: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """List files from the user's Google Drive."""
        access_token = self._get_valid_access_token(install_id)

        if not folder_id:
            folder_id = self.get_config_value(install_id, "root_folder_id") or None

        files_data = google_drive.list_files(
            access_token=access_token,
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
        install_id = kwargs.get("install_id")
        if not install_id:
            raise ValueError("install_id required for download")
        access_token = self._get_valid_access_token(install_id)
        return google_drive.download_file(access_token, file_id)

    # sync_file is inherited from ConnectorService — it automatically
    # passes install_id to download_file via **download_kwargs.
