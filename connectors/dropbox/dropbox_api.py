"""
Dropbox API operations using OAuth2 authentication.

Provides functions for OAuth flow, file listing, and file downloading
from Dropbox using user-authorized access tokens.
"""

import json
import requests
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlencode

_API_TIMEOUT = 30        # metadata, OAuth, list operations
_DOWNLOAD_TIMEOUT = 300  # content download — 5 min for large files

DROPBOX_AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
DROPBOX_TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"
DROPBOX_API_URL = "https://api.dropboxapi.com/2"
DROPBOX_CONTENT_URL = "https://content.dropboxapi.com/2"

DROPBOX_SCOPES = [
    "account_info.read",
    "files.metadata.read",
    "files.content.read",
]

SUPPORTED_EXTENSIONS = [".pdf", ".md", ".markdown", ".jpg", ".jpeg", ".png", ".webp"]

MIME_MAP = {
    "pdf": "application/pdf",
    "md": "text/markdown",
    "markdown": "text/markdown",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


# ------------------------------------------------------------------ #
# OAuth helpers                                                        #
# ------------------------------------------------------------------ #

def build_auth_url(client_id: str, redirect_uri: str, state: str = "") -> str:
    """Build the Dropbox OAuth2 authorization URL."""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "token_access_type": "offline",
    }
    if state:
        params["state"] = state
    return f"{DROPBOX_AUTH_URL}?{urlencode(params)}"


def exchange_code(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> Dict[str, Any]:
    """Exchange an authorization code for access + refresh tokens."""
    resp = requests.post(
        DROPBOX_TOKEN_URL,
        data={
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        auth=(client_id, client_secret),
        timeout=_API_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> Dict[str, Any]:
    """Refresh an expired access token."""
    resp = requests.post(
        DROPBOX_TOKEN_URL,
        data={
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        auth=(client_id, client_secret),
        timeout=_API_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def get_user_info(access_token: str) -> Dict[str, Any]:
    """Get the authenticated user's email and profile info."""
    resp = requests.post(
        f"{DROPBOX_API_URL}/users/get_current_account",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=_API_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    data["display_name"] = data.get("name", {}).get("display_name")
    return data


def revoke_token(access_token: str) -> bool:
    """Revoke an access token."""
    try:
        resp = requests.post(
            f"{DROPBOX_API_URL}/auth/token/revoke",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=_API_TIMEOUT,
        )
        return resp.status_code == 200
    except Exception:
        return False


# ------------------------------------------------------------------ #
# Dropbox file operations                                              #
# ------------------------------------------------------------------ #

def list_files(
    access_token: str,
    folder_path: Optional[str] = None,
    cursor: Optional[str] = None,
    page_size: int = 50,
) -> dict:
    """List files from Dropbox using an access token."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    if cursor:
        response = requests.post(
            f"{DROPBOX_API_URL}/files/list_folder/continue",
            headers=headers,
            json={"cursor": cursor},
            timeout=_API_TIMEOUT,
        )
    else:
        path = folder_path if folder_path else ""
        response = requests.post(
            f"{DROPBOX_API_URL}/files/list_folder",
            headers=headers,
            json={"path": path, "limit": page_size},
            timeout=_API_TIMEOUT,
        )

    response.raise_for_status()
    data = response.json()

    files = []
    for entry in data.get("entries", []):
        is_folder = entry.get(".tag") == "folder"
        name = entry.get("name", "")
        extension = name.lower().rsplit(".", 1)[-1] if "." in name else ""

        # Filter by supported extensions (skip unsupported files, include folders)
        if not is_folder and f".{extension}" not in SUPPORTED_EXTENSIONS:
            continue

        files.append({
            "id": entry.get("id") if is_folder else entry.get("path_lower"),
            "name": name,
            "mimeType": "folder" if is_folder else MIME_MAP.get(extension),
            "size": entry.get("size") if not is_folder else None,
            "modifiedTime": entry.get("server_modified"),
            "isFolder": is_folder,
        })

    return {
        "files": files,
        "nextPageToken": data.get("cursor") if data.get("has_more") else None,
    }


def download_file(access_token: str, file_path: str) -> Tuple[bytes, str, str]:
    """Download a file from Dropbox using an access token."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": json.dumps({"path": file_path}),
    }

    response = requests.post(
        f"{DROPBOX_CONTENT_URL}/files/download",
        headers=headers,
        timeout=_DOWNLOAD_TIMEOUT,
    )
    response.raise_for_status()

    # Get metadata from response header
    api_result = json.loads(response.headers.get("Dropbox-API-Result", "{}"))
    file_name = api_result.get("name", file_path.split("/")[-1])

    # Determine mime type from extension
    extension = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
    mime_type = MIME_MAP.get(extension, "application/octet-stream")

    return response.content, file_name, mime_type
