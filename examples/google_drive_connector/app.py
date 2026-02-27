"""
Google Drive Connector — Ask DIANA Marketplace Extension

A standalone Flask app that:
1. Receives install/uninstall webhooks from Ask DIANA
2. Manages its own Google OAuth flow for connecting Google Drive
3. Lists files from Google Drive
4. Downloads files and uploads them to Ask DIANA via the Extension API

Run:
    export ASKDIANA_API_KEY="askd_your_key"
    export ASKDIANA_BASE_URL="https://app.askdiana.ai"
    export WEBHOOK_SIGNING_SECRET="your-secret"
    export GOOGLE_CLIENT_ID="your-google-client-id"
    export GOOGLE_CLIENT_SECRET="your-google-client-secret"
    export EXTENSION_BASE_URL="https://your-ngrok-url.ngrok.io"
    python app.py
"""

import os
import sys
import logging
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, redirect

# Import SDK from parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from askdiana import AskDianaClient, verify_webhook, WebhookVerificationError

import google_drive
import database

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

API_KEY = os.environ.get("ASKDIANA_API_KEY", "")
BASE_URL = os.environ.get("ASKDIANA_BASE_URL", "https://app.askdiana.ai")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SIGNING_SECRET", "")

client = AskDianaClient(api_key=API_KEY, base_url=BASE_URL)

database.init_db()


def _verify(req):
    """Verify webhook signature."""
    verify_webhook(
        request_body=req.get_data(),
        signature_header=req.headers.get("X-AskDiana-Signature", ""),
        secret=WEBHOOK_SECRET,
        timestamp_header=req.headers.get("X-AskDiana-Delivery-Timestamp"),
    )


def _get_valid_token(account: dict, account_id: int) -> str:
    """Get a valid access token, refreshing and persisting if needed."""
    result = google_drive.ensure_valid_token(account)
    if isinstance(result, tuple):
        new_token, token_data = result
        expires_at = None
        if token_data.get("expires_in"):
            expires_at = (
                datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            ).isoformat()
        database.update_tokens(
            account_id=account_id,
            access_token=new_token,
            refresh_token=token_data.get("refresh_token"),
            expires_at=expires_at,
        )
        return new_token
    return result


# ================================================================
# Webhook Handlers
# ================================================================

@app.route("/webhooks/install", methods=["POST"])
def on_install():
    """Handle extension.installed — save the install context."""
    try:
        _verify(request)
    except WebhookVerificationError as e:
        return jsonify({"error": str(e)}), 401

    body = request.get_json()
    data = body.get("data", {})
    install_id = data["install_id"]

    database.save_install(
        install_id=install_id,
        user_id=data.get("user_id", ""),
        tenant_id=data.get("tenant_id", ""),
        scopes_granted=data.get("scopes_granted", []),
    )
    logger.info(f"Extension installed: {install_id}")

    return jsonify({"ok": True}), 200


@app.route("/webhooks/uninstall", methods=["POST"])
def on_uninstall():
    """Handle extension.uninstalled — clean up stored data."""
    try:
        _verify(request)
    except WebhookVerificationError as e:
        return jsonify({"error": str(e)}), 401

    body = request.get_json()
    install_id = body.get("data", {}).get("install_id")
    if install_id:
        database.remove_install(install_id)
        logger.info(f"Extension uninstalled: {install_id}")

    return jsonify({"ok": True}), 200


@app.route("/webhooks/events", methods=["POST"])
def on_event():
    """Handle general events."""
    try:
        _verify(request)
    except WebhookVerificationError as e:
        return jsonify({"error": str(e)}), 401

    body = request.get_json()
    logger.info(f"Event: {body.get('event')}")
    return jsonify({"ok": True}), 200


# ================================================================
# Google OAuth Flow
# ================================================================

@app.route("/oauth/start", methods=["GET"])
def oauth_start():
    """Redirect user to Google OAuth consent screen."""
    install_id = request.args.get("install_id")
    if not install_id:
        return jsonify({"error": "install_id query parameter required"}), 400

    install = database.get_install(install_id)
    if not install:
        return jsonify({"error": "Unknown install_id — install the extension first"}), 404

    auth_url = google_drive.get_oauth_url(install_id)
    return redirect(auth_url)


@app.route("/oauth/callback", methods=["GET"])
def oauth_callback():
    """Handle Google OAuth callback — exchange code, store tokens."""
    code = request.args.get("code")
    state = request.args.get("state")  # install_id
    error = request.args.get("error")

    if error:
        logger.warning(f"OAuth error: {error}")
        return jsonify({"error": f"OAuth denied: {error}"}), 400

    if not code or not state:
        return jsonify({"error": "Missing code or state parameter"}), 400

    install_id = state
    install = database.get_install(install_id)
    if not install:
        return jsonify({"error": "Unknown install"}), 404

    try:
        tokens = google_drive.exchange_code(code)
        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token")
        expires_in = tokens.get("expires_in")

        user_info = google_drive.get_user_info(access_token)
        email = user_info.get("email", "unknown")
        display_name = user_info.get("name", "")
        google_user_id = user_info.get("id", "")

        token_expires_at = None
        if expires_in:
            token_expires_at = (
                datetime.utcnow() + timedelta(seconds=expires_in)
            ).isoformat()

        database.save_google_account(
            install_id=install_id,
            email=email,
            display_name=display_name,
            google_user_id=google_user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
        )

        logger.info(f"Google account connected: {email} for install {install_id}")
        return jsonify({"success": True, "message": f"Connected {email}", "email": email}), 200

    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ================================================================
# API Endpoints
# ================================================================

@app.route("/api/accounts", methods=["GET"])
def list_accounts():
    """List connected Google accounts for an install."""
    install_id = request.args.get("install_id")
    if not install_id:
        return jsonify({"error": "install_id required"}), 400

    accounts = database.get_google_accounts(install_id)
    return jsonify({"success": True, "accounts": accounts}), 200


@app.route("/api/files", methods=["GET"])
def api_list_files():
    """List files from a connected Google Drive account."""
    install_id = request.args.get("install_id")
    account_id = request.args.get("account_id")
    folder_id = request.args.get("folder_id")
    page_token = request.args.get("page_token")

    if not install_id or not account_id:
        return jsonify({"error": "install_id and account_id required"}), 400

    account = database.get_google_account(int(account_id))
    if not account or account["install_id"] != install_id:
        return jsonify({"error": "Account not found"}), 404

    try:
        access_token = _get_valid_token(account, int(account_id))

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

        return jsonify({
            "success": True,
            "files": files,
            "nextPageToken": files_data.get("nextPageToken"),
        }), 200

    except Exception as e:
        logger.error(f"List files error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/sync", methods=["POST"])
def sync_file():
    """Download a file from Google Drive and upload to Ask DIANA.

    Request body::

        {
            "install_id": "uuid",
            "account_id": 1,
            "file_id": "google_drive_file_id"
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    install_id = data.get("install_id")
    account_id = data.get("account_id")
    file_id = data.get("file_id")

    if not all([install_id, account_id, file_id]):
        return jsonify({"error": "install_id, account_id, and file_id required"}), 400

    account = database.get_google_account(int(account_id))
    if not account or account["install_id"] != install_id:
        return jsonify({"error": "Account not found"}), 404

    file_name = file_id  # fallback
    try:
        # 1. Ensure valid token
        access_token = _get_valid_token(account, int(account_id))

        # 2. Download from Google Drive
        logger.info(f"Downloading {file_id} from Google Drive...")
        content, file_name, mime_type = google_drive.download_file(access_token, file_id)
        logger.info(f"Downloaded: {file_name} ({len(content)} bytes, {mime_type})")

        # 3. Upload to Ask DIANA via SDK
        logger.info(f"Uploading {file_name} to Ask DIANA...")
        result = client.upload_document(
            install_id=install_id,
            file_content=content,
            file_name=file_name,
            source_type="google_drive",
            source_reference=file_id,
        )

        # 4. Record sync
        doc_id = result.get("document", {}).get("id") if result.get("success") else None
        database.record_sync(
            install_id=install_id,
            google_account_id=int(account_id),
            google_file_id=file_id,
            file_name=file_name,
            askdiana_document_id=doc_id,
            status="success" if result.get("success") else "error",
        )

        logger.info(f"Sync complete: {file_name} -> doc {doc_id}")
        return jsonify({
            "success": True,
            "file_name": file_name,
            "document": result.get("document"),
        }), 200

    except Exception as e:
        logger.error(f"Sync error: {e}", exc_info=True)
        database.record_sync(
            install_id=install_id,
            google_account_id=int(account_id),
            google_file_id=file_id,
            file_name=file_name,
            askdiana_document_id=None,
            status="error",
            error_message=str(e),
        )
        return jsonify({"error": str(e)}), 500


@app.route("/api/sync/history", methods=["GET"])
def sync_history():
    """Get sync history for an install."""
    install_id = request.args.get("install_id")
    if not install_id:
        return jsonify({"error": "install_id required"}), 400

    history = database.get_sync_history(install_id)
    return jsonify({"success": True, "history": history}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5004))
    app.run(port=port, debug=True)
