"""
NoteService -- business logic for note.
"""

import uuid
from datetime import datetime, timezone
from askdiana import ExtensionService


class NoteService(ExtensionService):
    NAMESPACE = "notes"

    def create_note(self, install_id, title, content=""):
        note_id = str(uuid.uuid4())
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "pinned": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.client.set_data(install_id, self.NAMESPACE, note_id, note)
        return note

    def list_notes(self, install_id):
        result = self.client.list_data(install_id, self.NAMESPACE)
        notes = [item["value"] for item in result.get("data", [])]
        notes.sort(key=lambda n: (not n.get("pinned", False), n.get("created_at", "")))
        return notes

    def get_note(self, install_id, note_id):
        result = self.client.get_data(install_id, self.NAMESPACE, note_id)
        return result.get("data", {}).get("value")

    def update_note(self, install_id, note_id, title=None, content=None, pinned=None):
        existing = self.get_note(install_id, note_id)
        if not existing:
            return None
        if title is not None:
            existing["title"] = title
        if content is not None:
            existing["content"] = content
        if pinned is not None:
            existing["pinned"] = pinned
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.client.set_data(install_id, self.NAMESPACE, note_id, existing)
        return existing

    def delete_note(self, install_id, note_id):
        self.client.delete_data(install_id, self.NAMESPACE, note_id)
