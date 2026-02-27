"""
Google Drive OAuth and API operations.

Extracted from Ask DIANA's built-in cloud connector
(ask-backend-python/services/cloud_connector.py).
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlencode

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
EXTENSION_BASE_URL = os.environ.get("EXTENSION_BASE_URL", "")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

SUPPORTED_MIME_TYPES = [
    "application/pdf",
    "text/markdown",
    "text/x-markdown",
    "image/jpeg",
    "image/png",
    "image/webp",
]


def get_oauth_url(install_id: str) -> str:
    """Generate Google OAuth authorization URL.

    ``install_id`` is passed in the ``state`` parameter so the callback
    can associate the authorization with the correct Ask DIANA install.
    """
    redirect_uri = f"{EXTENSION_BASE_URL}/oauth/callback"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": install_id,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    redirect_uri = f"{EXTENSION_BASE_URL}/oauth/callback"
    response = requests.post(GOOGLE_TOKEN_URL, data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    })
    response.raise_for_status()
    return response.json()


def refresh_access_token(refresh_token: str) -> Optional[dict]:
    """Refresh an expired access token. Returns ``None`` on failure."""
    response = requests.post(GOOGLE_TOKEN_URL, data={
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    })
    if response.status_code == 200:
        return response.json()
    return None


def get_user_info(access_token: str) -> dict:
    """Get Google user profile (email, name, id)."""
    response = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()


def list_files(
    access_token: str,
    folder_id: Optional[str] = None,
    page_token: Optional[str] = None,
    page_size: int = 50,
) -> dict:
    """List files from Google Drive (only supported types + folders)."""
    mime_query = " or ".join(f"mimeType='{mt}'" for mt in SUPPORTED_MIME_TYPES)
    mime_query = f"({mime_query} or mimeType='application/vnd.google-apps.folder')"

    parent = folder_id or "root"
    query = f"'{parent}' in parents and {mime_query} and trashed=false"

    params = {
        "q": query,
        "pageSize": page_size,
        "fields": "nextPageToken, files(id, name, mimeType, size, modifiedTime)",
        "orderBy": "folder,name",
    }
    if page_token:
        params["pageToken"] = page_token

    response = requests.get(
        GOOGLE_DRIVE_FILES_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
    )
    response.raise_for_status()
    return response.json()


def download_file(access_token: str, file_id: str) -> Tuple[bytes, str, str]:
    """Download a file from Google Drive.

    Returns:
        (content_bytes, file_name, mime_type)
    """
    # Get metadata
    meta_resp = requests.get(
        f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"fields": "name,mimeType,size"},
    )
    meta_resp.raise_for_status()
    metadata = meta_resp.json()

    # Download content
    content_resp = requests.get(
        f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"alt": "media"},
    )
    content_resp.raise_for_status()

    return (
        content_resp.content,
        metadata["name"],
        metadata.get("mimeType", "application/octet-stream"),
    )


def ensure_valid_token(account: dict):
    """Check if token is expired and refresh if needed.

    Returns:
        str — valid access token (if no refresh was needed)
        tuple(str, dict) — (new_access_token, token_data) if refreshed

    Raises:
        ValueError if refresh fails.
    """
    expires_at = account.get("token_expires_at")
    if expires_at:
        try:
            expiry = datetime.fromisoformat(expires_at)
            if expiry > datetime.utcnow() + timedelta(minutes=5):
                return account["access_token"]
        except (ValueError, TypeError):
            pass  # treat as expired

    # Refresh needed
    refresh_token = account.get("refresh_token")
    if not refresh_token:
        raise ValueError("No refresh token available. User needs to re-authenticate.")

    token_data = refresh_access_token(refresh_token)
    if not token_data:
        raise ValueError("Token refresh failed. User needs to re-authenticate.")

    return token_data["access_token"], token_data
