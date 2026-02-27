"""
notes controller -- Flask Blueprint with routes.
"""

from flask import Blueprint, request, jsonify, g, current_app
from askdiana.controller import install_id_required
try:
    from notes_app.services.note_service import NoteService
except ImportError:
    from services.note_service import NoteService

notes_bp = Blueprint("notes", __name__)


def _get_service():
    ext_app = current_app.config.get("ext_app")
    return NoteService(ext_app.client)


@notes_bp.route("/api/notes", methods=["GET"])
@install_id_required
def list_notes():
    """List all notes for the install. Pass ?install_id=<id>"""
    svc = _get_service()
    notes = svc.list_notes(g.install_id)
    return jsonify({"success": True, "notes": notes}), 200


@notes_bp.route("/api/notes", methods=["POST"])
@install_id_required
def create_note():
    """Create a note. Body: {"install_id": "...", "title": "...", "content": "..."}"""
    body = request.get_json()
    if not body or not body.get("title"):
        return jsonify({"success": False, "error": "title is required"}), 400
    svc = _get_service()
    note = svc.create_note(g.install_id, body["title"], body.get("content", ""))
    return jsonify({"success": True, "note": note}), 201


@notes_bp.route("/api/notes/<note_id>", methods=["GET"])
@install_id_required
def get_note(note_id):
    """Get a single note by ID. Pass ?install_id=<id>"""
    svc = _get_service()
    try:
        note = svc.get_note(g.install_id, note_id)
    except Exception:
        note = None
    if not note:
        return jsonify({"success": False, "error": "Note not found"}), 404
    return jsonify({"success": True, "note": note}), 200


@notes_bp.route("/api/notes/<note_id>", methods=["PUT"])
@install_id_required
def update_note(note_id):
    """Update a note. Body: {"install_id": "...", "title": "...", "content": "...", "pinned": true}"""
    body = request.get_json() or {}
    svc = _get_service()
    note = svc.update_note(
        g.install_id,
        note_id,
        title=body.get("title"),
        content=body.get("content"),
        pinned=body.get("pinned"),
    )
    if not note:
        return jsonify({"success": False, "error": "Note not found"}), 404
    return jsonify({"success": True, "note": note}), 200


@notes_bp.route("/api/notes/<note_id>", methods=["DELETE"])
@install_id_required
def delete_note(note_id):
    """Delete a note. Pass ?install_id=<id>"""
    svc = _get_service()
    try:
        svc.delete_note(g.install_id, note_id)
    except Exception:
        return jsonify({"success": False, "error": "Note not found"}), 404
    return jsonify({"success": True, "message": "Note deleted"}), 200
