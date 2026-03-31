"""
Google Drive API operations using OAuth2 authentication.

Provides functions for OAuth flow, file listing, and file downloading
from Google Drive using user-authorized access tokens.
"""

import requests
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlencode

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"

DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]

SUPPORTED_MIME_TYPES = [
    "application/pdf",
    "text/markdown",
    "text/x-markdown",
    "text/plain",
    "image/jpeg",
    "image/png",
    "image/webp",
]


# ------------------------------------------------------------------ #
# OAuth helpers                                                        #
# ------------------------------------------------------------------ #

def build_auth_url(client_id: str, redirect_uri: str, state: str = "") -> str:
    """Build the Google OAuth2 authorization URL."""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(DRIVE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> Dict[str, Any]:
    """Exchange an authorization code for access + refresh tokens."""
    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    })
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> Dict[str, Any]:
    """Refresh an expired access token."""
    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
    })
    resp.raise_for_status()
    return resp.json()


def get_user_info(access_token: str) -> Dict[str, Any]:
    """Get the authenticated user's email and profile info."""
    resp = requests.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    return resp.json()


def revoke_token(token: str) -> bool:
    """Revoke an access or refresh token."""
    try:
        resp = requests.post(GOOGLE_REVOKE_URL, params={"token": token})
        return resp.status_code == 200
    except Exception:
        return False


# ------------------------------------------------------------------ #
# Drive file operations                                                #
# ------------------------------------------------------------------ #

def list_files(
    access_token: str,
    folder_id: Optional[str] = None,
    page_token: Optional[str] = None,
    page_size: int = 50,
) -> dict:
    """List files from Google Drive using an access token."""
    mime_query = " or ".join(f"mimeType='{mt}'" for mt in SUPPORTED_MIME_TYPES)
    mime_query = f"({mime_query} or mimeType='application/vnd.google-apps.folder')"

    if folder_id:
        query = f"'{folder_id}' in parents and {mime_query} and trashed=false"
    else:
        query = f"'root' in parents and {mime_query} and trashed=false"

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
        params=params,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()


def download_file(access_token: str, file_id: str) -> Tuple[bytes, str, str]:
    """Download a file from Google Drive using an access token."""
    headers = {"Authorization": f"Bearer {access_token}"}

    # Get metadata
    meta_resp = requests.get(
        f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
        params={"fields": "name,mimeType,size"},
        headers=headers,
    )
    meta_resp.raise_for_status()
    metadata = meta_resp.json()

    # Download content
    content_resp = requests.get(
        f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
        params={"alt": "media"},
        headers=headers,
    )
    content_resp.raise_for_status()

    return (
        content_resp.content,
        metadata["name"],
        metadata.get("mimeType", "application/octet-stream"),
    )
