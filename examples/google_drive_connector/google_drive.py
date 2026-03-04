"""
Google Drive API operations using API key authentication.

API keys can access publicly shared files in Google Drive.
For private files, OAuth is required (see the OAuth example).
"""

import requests
from typing import Optional, Tuple

GOOGLE_DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"

SUPPORTED_MIME_TYPES = [
    "application/pdf",
    "text/markdown",
    "text/x-markdown",
    "text/plain",
    "image/jpeg",
    "image/png",
    "image/webp",
]


def list_files(
    api_key: str,
    folder_id: Optional[str] = None,
    page_token: Optional[str] = None,
    page_size: int = 50,
) -> dict:
    """List publicly shared files from Google Drive.

    Args:
        api_key: Google API key from Cloud Console.
        folder_id: Shared folder ID to list from. Defaults to searching
            all publicly accessible files.
        page_token: Pagination token from a previous response.
        page_size: Number of results per page (max 100).

    Returns:
        Google Drive API response with ``files`` list and optional
        ``nextPageToken``.
    """
    mime_query = " or ".join(f"mimeType='{mt}'" for mt in SUPPORTED_MIME_TYPES)
    mime_query = f"({mime_query} or mimeType='application/vnd.google-apps.folder')"

    if folder_id:
        query = f"'{folder_id}' in parents and {mime_query} and trashed=false"
    else:
        query = f"{mime_query} and trashed=false"

    params = {
        "q": query,
        "pageSize": page_size,
        "fields": "nextPageToken, files(id, name, mimeType, size, modifiedTime)",
        "orderBy": "folder,name",
        "key": api_key,
    }
    if page_token:
        params["pageToken"] = page_token

    response = requests.get(GOOGLE_DRIVE_FILES_URL, params=params)
    response.raise_for_status()
    return response.json()


def download_file(api_key: str, file_id: str) -> Tuple[bytes, str, str]:
    """Download a publicly shared file from Google Drive.

    Args:
        api_key: Google API key.
        file_id: The Google Drive file ID.

    Returns:
        Tuple of (content_bytes, file_name, mime_type).
    """
    # Get metadata
    meta_resp = requests.get(
        f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
        params={"fields": "name,mimeType,size", "key": api_key},
    )
    meta_resp.raise_for_status()
    metadata = meta_resp.json()

    # Download content
    content_resp = requests.get(
        f"{GOOGLE_DRIVE_FILES_URL}/{file_id}",
        params={"alt": "media", "key": api_key},
    )
    content_resp.raise_for_status()

    return (
        content_resp.content,
        metadata["name"],
        metadata.get("mimeType", "application/octet-stream"),
    )
