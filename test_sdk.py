"""
Quick test script for askdiana SDK features.
Run from the SDK root: python test_sdk.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("1. MODELS & FIELDS")
print("=" * 60)

from askdiana import (
    ExtModel, StringField, TextField, IntegerField,
    FloatField, BooleanField, DateTimeField, JsonField,
    register_all_models,
)

class TaskTracker(ExtModel):
    __tablename__ = "ext_myapp_tasks"

    id = StringField(primary_key=True, max_length=36)
    install_id = StringField(max_length=36, nullable=False)
    title = StringField(max_length=500, nullable=False)
    created_at = DateTimeField(nullable=True)

print(f"TaskTracker fields: {[f.name for f in TaskTracker._fields]}")
print(f"TaskTracker schema:")
import json
print(json.dumps(TaskTracker.to_schema(), indent=2))

print()
print("=" * 60)
print("2. MODEL INHERITANCE")
print("=" * 60)

class CompletableTask(TaskTracker):
    """Extends TaskTracker with completion fields."""
    __tablename__ = "ext_myapp_tasks"  # same table, extended

    description = TextField(nullable=True)
    priority = IntegerField(nullable=True)
    completed = BooleanField(nullable=True)
    metadata = JsonField(nullable=True)

print(f"CompletableTask fields: {[f.name for f in CompletableTask._fields]}")
print(f"Inherited from TaskTracker: {[f.name for f in TaskTracker._fields]}")
print(f"CompletableTask schema:")
print(json.dumps(CompletableTask.to_schema(), indent=2))

# Verify inheritance works correctly
assert len(CompletableTask._fields) == 8, f"Expected 8 fields, got {len(CompletableTask._fields)}"
assert len(TaskTracker._fields) == 4, "Parent should still have 4 fields"
print("\nInheritance: OK (child=8 fields, parent=4 fields)")

print()
print("=" * 60)
print("3. FIELD OVERRIDE IN CHILD")
print("=" * 60)

class StrictTask(TaskTracker):
    __tablename__ = "ext_myapp_strict_tasks"
    # Override parent's title to be longer
    title = StringField(max_length=1000, nullable=False)
    status = StringField(max_length=50, nullable=False)

print(f"StrictTask fields: {[f.name for f in StrictTask._fields]}")
title_col = [c for c in StrictTask.to_schema()["tables"][0]["columns"] if c["name"] == "title"][0]
print(f"title max_length overridden: {title_col['max_length']} (was 500 in parent)")
assert title_col["max_length"] == 1000
print("Field override: OK")

print()
print("=" * 60)
print("4. SCHEMA VALIDATION (CLI rules)")
print("=" * 60)

from askdiana.cli import _validate_schema

# Valid schema
schema = CompletableTask.to_schema()
errors = _validate_schema(schema)
print(f"Valid schema errors: {errors}")
assert errors == [], f"Expected no errors, got {errors}"

# Invalid: no ext_ prefix
bad_schema = {"tables": [{"name": "my_table", "columns": [{"name": "id", "type": "string", "primary_key": True}]}]}
errors = _validate_schema(bad_schema)
print(f"Bad prefix errors: {errors}")
assert any("ext_" in e for e in errors)

# Invalid: no primary key
bad_schema2 = {"tables": [{"name": "ext_test", "columns": [{"name": "name", "type": "string"}]}]}
errors = _validate_schema(bad_schema2)
print(f"No PK errors: {errors}")
assert any("primary key" in e for e in errors)

# Invalid: bad column type
bad_schema3 = {"tables": [{"name": "ext_test", "columns": [{"name": "id", "type": "uuid", "primary_key": True}]}]}
errors = _validate_schema(bad_schema3)
print(f"Bad type errors: {errors}")
assert any("not allowed" in e for e in errors)

print("Validation: OK")

print()
print("=" * 60)
print("5. EXTENSION SERVICE")
print("=" * 60)

from askdiana import ExtensionService

class TaskService(ExtensionService):
    def create_task(self, install_id, title, priority=3):
        return {"action": "set_data", "install_id": install_id, "title": title, "priority": priority}

# We can't call the real API, but we can verify the class works
print(f"TaskService base class: {TaskService.__bases__}")
print(f"TaskService has client attr: {'client' in TaskService.__init__.__code__.co_varnames}")
print("ExtensionService: OK")

print()
print("=" * 60)
print("6. AUTO-DISCOVERY")
print("=" * 60)

# Test discovery with the task_manager example
from askdiana.discovery import discover_models

# Add example to path
example_path = os.path.join(os.path.dirname(__file__), "examples")
if example_path not in sys.path:
    sys.path.insert(0, example_path)

models = discover_models("task_manager.models")
print(f"Discovered models from task_manager: {[m.__name__ for m in models]}")

print()
print("=" * 60)
print("7. EXTENSION APP (requires Flask)")
print("=" * 60)

try:
    from askdiana import ExtensionApp

    # Create app without API key (no real API calls)
    # Use __name__ so Flask can resolve root path from this script
    app = ExtensionApp(
        __name__,
        auto_discover=False,
        api_key=None,
    )

    # Register models manually
    app.register_model(TaskTracker)
    app.register_model(CompletableTask)
    print(f"Registered models: {[m.__name__ for m in app.models]}")

    # Test health endpoint
    with app.flask.test_client() as client:
        resp = client.get("/health")
        print(f"GET /health -> {resp.status_code} {resp.get_json()}")
        assert resp.status_code == 200

    print("ExtensionApp: OK")

except ImportError:
    print("Flask not installed -- skipping ExtensionApp test")
    print("Install with: pip install flask")

print()
print("=" * 60)
print("8. CONTROLLER DECORATORS (requires Flask)")
print("=" * 60)

try:
    from flask import Flask, Blueprint
    from askdiana.controller import webhook_required, install_id_required

    test_app = Flask(__name__)
    test_bp = Blueprint("test", __name__)

    @test_bp.route("/api/items", methods=["GET"])
    @install_id_required
    def list_items():
        from flask import g, jsonify
        return jsonify({"install_id": g.install_id, "items": []}), 200

    test_app.register_blueprint(test_bp)

    with test_app.test_client() as client:
        # Without install_id -> 400
        resp = client.get("/api/items")
        print(f"GET /api/items (no install_id) -> {resp.status_code}")
        assert resp.status_code == 400

        # With install_id -> 200
        resp = client.get("/api/items?install_id=test-123")
        print(f"GET /api/items?install_id=test-123 -> {resp.status_code} {resp.get_json()}")
        assert resp.status_code == 200
        assert resp.get_json()["install_id"] == "test-123"

    print("Controller decorators: OK")

except ImportError:
    print("Flask not installed -- skipping controller test")

print()
print("=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)
