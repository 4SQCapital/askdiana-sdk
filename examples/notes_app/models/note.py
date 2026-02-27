"""
Note model.
"""

from askdiana import ExtModel, StringField, TextField, DateTimeField, BooleanField


class Note(ExtModel):
    __tablename__ = "ext_notes_items"

    id = StringField(primary_key=True, max_length=36)
    install_id = StringField(max_length=36, nullable=False)
    title = StringField(max_length=500, nullable=False)
    content = TextField(nullable=True)
    pinned = BooleanField(nullable=True)
    created_at = DateTimeField(nullable=True)
