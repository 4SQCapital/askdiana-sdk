"""
Microsoft OneDrive API operations using OAuth2 authentication.

Provides functions for OAuth flow, file listing, and file downloading
from OneDrive using Microsoft Graph API with user-authorized access tokens.
"""

import requests
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlencode

MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0"

ONEDRIVE_SCOPES = [
    "Files.Read",
    "User.Read",
    "offline_access",
]

SUPPORTED_EXTENSIONS = [".pdf", ".md", ".markdown", ".jpg", ".jpeg", ".png", ".webp"]


# ------------------------------------------------------------------ #
# OAuth helpers                                                        #
# ------------------------------------------------------------------ #

def build_auth_url(client_id: str, redirect_uri: str, state: str = "") -> str:
    """Build the Microsoft OAuth2 authorization URL."""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(ONEDRIVE_SCOPES),
        "response_mode": "query",
    }
    if state:
        params["state"] = state
    return f"{MICROSOFT_AUTH_URL}?{urlencode(params)}"


def exchange_code(
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> Dict[str, Any]:
    """Exchange an authorization code for access + refresh tokens."""
    resp = requests.post(MICROSOFT_TOKEN_URL, data={
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
        "scope": " ".join(ONEDRIVE_SCOPES),
    })
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> Dict[str, Any]:
    """Refresh an expired access token."""
    resp = requests.post(MICROSOFT_TOKEN_URL, data={
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "scope": " ".join(ONEDRIVE_SCOPES),
    })
    resp.raise_for_status()
    return resp.json()


def get_user_info(access_token: str) -> Dict[str, Any]:
    """Get the authenticated user's email and profile info."""
    resp = requests.get(
        f"{GRAPH_API_URL}/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    data = resp.json()
    # Microsoft returns mail or userPrincipalName for email
    data["email"] = data.get("mail") or data.get("userPrincipalName")
    return data


# ------------------------------------------------------------------ #
# OneDrive file operations                                             #
# ------------------------------------------------------------------ #

def list_files(
    access_token: str,
    folder_id: Optional[str] = None,
    page_token: Optional[str] = None,
    page_size: int = 50,
) -> dict:
    """List files from OneDrive using an access token."""
    headers = {"Authorization": f"Bearer {access_token}"}

    if page_token:
        # page_token is the full @odata.nextLink URL
        response = requests.get(page_token, headers=headers)
    else:
        if folder_id:
            url = f"{GRAPH_API_URL}/me/drive/items/{folder_id}/children"
        else:
            url = f"{GRAPH_API_URL}/me/drive/root/children"
        response = requests.get(url, headers=headers, params={"$top": page_size})

    response.raise_for_status()
    data = response.json()

    files = []
    for item in data.get("value", []):
        is_folder = "folder" in item
        name = item.get("name", "")
        extension = name.lower().rsplit(".", 1)[-1] if "." in name else ""

        # Filter by supported extensions (skip unsupported files, include folders)
        if not is_folder and f".{extension}" not in SUPPORTED_EXTENSIONS:
            continue

        files.append({
            "id": item.get("id"),
            "name": name,
            "mimeType": item.get("file", {}).get("mimeType") if not is_folder else "folder",
            "size": item.get("size") if not is_folder else None,
            "modifiedTime": item.get("lastModifiedDateTime"),
            "isFolder": is_folder,
        })

    return {
        "files": files,
        "nextPageToken": data.get("@odata.nextLink"),
    }


def download_file(access_token: str, file_id: str) -> Tuple[bytes, str, str]:
    """Download a file from OneDrive using an access token."""
    headers = {"Authorization": f"Bearer {access_token}"}

    # Get file metadata (includes @microsoft.graph.downloadUrl)
    meta_resp = requests.get(
        f"{GRAPH_API_URL}/me/drive/items/{file_id}",
        headers=headers,
    )
    meta_resp.raise_for_status()
    metadata = meta_resp.json()

    file_name = metadata.get("name")
    mime_type = metadata.get("file", {}).get("mimeType", "application/octet-stream")
    download_url = metadata.get("@microsoft.graph.downloadUrl")

    if not download_url:
        raise ValueError("No download URL available for this file")

    # Download file content
    content_resp = requests.get(download_url)
    content_resp.raise_for_status()

    return content_resp.content, file_name, mime_type
