"""
Extension database models for the Google Drive Connector.

These models declare tables in the ``ask_extensions`` database.
They are registered and applied via the SDK on first install.
"""

import os
import sys

# Import SDK from parent directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from askdiana import ExtModel, StringField, TextField, DateTimeField


class SyncHistory(ExtModel):
    """Tracks files synced from Google Drive to Ask DIANA."""

    __tablename__ = "ext_gdrive_sync_history"

    id = StringField(primary_key=True, max_length=36)
    install_id = StringField(max_length=36, nullable=False)
    google_file_id = StringField(max_length=255, nullable=False)
    file_name = StringField(max_length=500, nullable=False)
    askdiana_document_id = StringField(max_length=36, nullable=True)
    status = StringField(max_length=50, nullable=False)
    error_message = TextField(nullable=True)
    synced_at = DateTimeField(nullable=True)
