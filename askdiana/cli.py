"""
CLI tool for Ask DIANA extensions.

Usage::

    askdiana init my_extension
    askdiana scaffold model TaskTracker
    askdiana scaffold service task
    askdiana scaffold controller tasks
    askdiana db validate
    askdiana db schema
    askdiana db push --install-id <id> --version 1.0.0
"""

import argparse
import json
import os
import sys

# ------------------------------------------------------------------ #
# Templates                                                            #
# ------------------------------------------------------------------ #

APP_TEMPLATE = '''"""
{name} -- Ask DIANA Extension.
"""

import os
import logging

from dotenv import load_dotenv
load_dotenv()

from askdiana import ExtensionApp

logging.basicConfig(level=logging.INFO)

app = ExtensionApp(__name__)


@app.flask.route("/webhooks/install", methods=["POST"])
def on_install():
    from flask import request, jsonify
    app.verify_request()

    body = request.get_json()
    install_id = body["data"]["install_id"]

    # Register and apply all discovered models
    app.setup_models(install_id, version="1.0.0")

    return jsonify({{"ok": True}}), 200


@app.flask.route("/webhooks/uninstall", methods=["POST"])
def on_uninstall():
    from flask import request, jsonify
    app.verify_request()
    return jsonify({{"ok": True}}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(port=port, debug=True)
'''

MANIFEST_TEMPLATE = """{
  "name": "%(name)s",
  "slug": "%(slug)s",
  "version": "1.0.0",
  "type": "tool",
  "description": "TODO: describe your extension",
  "short_description": "TODO: short description",
  "permissions": [],
  "webhooks": {
    "on_install": "https://<your-url>/webhooks/install",
    "on_uninstall": "https://<your-url>/webhooks/uninstall"
  },
  "pricing": {
    "model": "free"
  }
}
"""

ENV_TEMPLATE = """ASKDIANA_API_KEY=askd_your_key_here
ASKDIANA_BASE_URL=https://app.askdiana.ai
WEBHOOK_SIGNING_SECRET=your-webhook-secret
"""

MODELS_INIT = '''"""Extension models -- discovered automatically by ExtensionApp."""
'''

SERVICES_INIT = '''"""Extension services -- business logic layer."""
'''

CONTROLLERS_INIT = '''"""Extension controllers -- Flask Blueprints, discovered automatically."""
'''

MODEL_TEMPLATE = '''"""
{class_name} model.
"""

from askdiana import ExtModel, StringField, IntegerField, DateTimeField


class {class_name}(ExtModel):
    """TODO: describe this model."""

    __tablename__ = "ext_{table_name}"

    id = StringField(primary_key=True, max_length=36)
    install_id = StringField(max_length=36, nullable=False)
    created_at = DateTimeField(nullable=True)
'''

SERVICE_TEMPLATE = '''"""
{class_name}Service -- business logic for {name}.
"""

from askdiana import ExtensionService


class {class_name}Service(ExtensionService):
    """TODO: implement business logic."""

    pass
'''

CONTROLLER_TEMPLATE = '''"""
{name} controller -- Flask Blueprint with routes.
"""

from flask import Blueprint, request, jsonify, g
from askdiana.controller import install_id_required

{bp_var} = Blueprint("{name}", __name__)


@{bp_var}.route("/api/{name}", methods=["GET"])
@install_id_required
def list_{name}():
    """TODO: implement."""
    return jsonify({{"success": True, "{name}": []}}), 200
'''


# ------------------------------------------------------------------ #
# Commands                                                             #
# ------------------------------------------------------------------ #


def cmd_init(args):
    """Create a new extension project directory."""
    name = args.name
    slug = name.lower().replace(" ", "_").replace("-", "_")
    base = os.path.join(os.getcwd(), name)

    if os.path.exists(base):
        print(f"Error: directory '{name}' already exists.", file=sys.stderr)
        sys.exit(1)

    for d in [
        base,
        os.path.join(base, "models"),
        os.path.join(base, "services"),
        os.path.join(base, "controllers"),
        os.path.join(base, "views"),
    ]:
        os.makedirs(d, exist_ok=True)

    _write(os.path.join(base, "app.py"), APP_TEMPLATE.format(name=name))
    _write(os.path.join(base, "manifest.json"), MANIFEST_TEMPLATE % {"name": name, "slug": slug})
    _write(os.path.join(base, ".env.example"), ENV_TEMPLATE)
    _write(os.path.join(base, "requirements.txt"), "askdiana\nflask\npython-dotenv\n")
    _write(os.path.join(base, "models", "__init__.py"), MODELS_INIT)
    _write(os.path.join(base, "services", "__init__.py"), SERVICES_INIT)
    _write(os.path.join(base, "controllers", "__init__.py"), CONTROLLERS_INIT)
    _write(os.path.join(base, "views", "__init__.py"), "")

    print(f"Created extension project: {name}/")
    print(f"  cd {name}")
    print(f"  pip install askdiana[app]")
    print(f"  python app.py")


def cmd_scaffold(args):
    """Generate a model, service, or controller file."""
    kind = args.kind
    name = args.name

    if kind == "model":
        _scaffold_model(name)
    elif kind == "service":
        _scaffold_service(name)
    elif kind == "controller":
        _scaffold_controller(name)
    else:
        print(f"Unknown scaffold kind: {kind}", file=sys.stderr)
        sys.exit(1)


def _scaffold_model(name: str):
    class_name = _to_class_name(name)
    table_name = name.lower().replace(" ", "_")

    path = os.path.join(os.getcwd(), "models", f"{table_name}.py")
    _ensure_dir(path)
    _write(path, MODEL_TEMPLATE.format(class_name=class_name, table_name=table_name))
    print(f"Created model: models/{table_name}.py ({class_name})")


def _scaffold_service(name: str):
    class_name = _to_class_name(name)
    slug = name.lower().replace(" ", "_")

    path = os.path.join(os.getcwd(), "services", f"{slug}_service.py")
    _ensure_dir(path)
    _write(path, SERVICE_TEMPLATE.format(class_name=class_name, name=name))
    print(f"Created service: services/{slug}_service.py ({class_name}Service)")


def _scaffold_controller(name: str):
    slug = name.lower().replace(" ", "_")
    bp_var = f"{slug}_bp"

    path = os.path.join(os.getcwd(), "controllers", f"{slug}.py")
    _ensure_dir(path)
    _write(path, CONTROLLER_TEMPLATE.format(name=slug, bp_var=bp_var))
    print(f"Created controller: controllers/{slug}.py (Blueprint: {slug})")


# ------------------------------------------------------------------ #
# DB commands                                                          #
# ------------------------------------------------------------------ #

# Validation rules (mirrors backend extensions_schema_validator.py)
_ALLOWED_COLUMN_TYPES = {
    "string", "text", "integer", "float", "boolean",
    "datetime", "date", "json",
}
_RESERVED_TABLE_NAMES = {
    "extension_data", "extension_storage", "extension_schema_registry",
    "alembic_version",
}
_MAX_TABLE_NAME_LENGTH = 64
_MAX_COLUMNS_PER_TABLE = 50


def _validate_schema(schema: dict) -> list:
    """Validate a schema dict using the same rules as the backend.

    Returns a list of error strings (empty = valid).
    """
    errors = []
    tables = schema.get("tables", [])
    if not tables:
        errors.append("Schema must declare at least one table")
        return errors

    seen_tables = set()
    for table in tables:
        name = table.get("name", "")
        if not name:
            errors.append("Table name is required")
            continue
        if name in _RESERVED_TABLE_NAMES:
            errors.append(f"Table name '{name}' is reserved")
        if not name.startswith("ext_"):
            errors.append(f"Table name '{name}' must start with 'ext_' prefix")
        if len(name) > _MAX_TABLE_NAME_LENGTH:
            errors.append(f"Table name '{name}' exceeds {_MAX_TABLE_NAME_LENGTH} characters")
        if name in seen_tables:
            errors.append(f"Duplicate table name: '{name}'")
        seen_tables.add(name)

        columns = table.get("columns", [])
        if not columns:
            errors.append(f"Table '{name}' must have at least one column")
            continue
        if len(columns) > _MAX_COLUMNS_PER_TABLE:
            errors.append(f"Table '{name}' exceeds {_MAX_COLUMNS_PER_TABLE} column limit")

        has_pk = False
        seen_cols = set()
        for col in columns:
            col_name = col.get("name", "")
            col_type = col.get("type", "")
            if not col_name:
                errors.append(f"Table '{name}': column name is required")
            if col_name in seen_cols:
                errors.append(f"Table '{name}': duplicate column '{col_name}'")
            seen_cols.add(col_name)
            if col_type not in _ALLOWED_COLUMN_TYPES:
                errors.append(
                    f"Table '{name}', column '{col_name}': "
                    f"type '{col_type}' not allowed. "
                    f"Use: {', '.join(sorted(_ALLOWED_COLUMN_TYPES))}"
                )
            if col.get("primary_key"):
                has_pk = True
        if not has_pk:
            errors.append(f"Table '{name}' must have at least one primary key column")

    return errors


def _discover_local_models():
    """Discover ExtModel subclasses from the local models/ package."""
    cwd = os.getcwd()
    pkg_name = os.path.basename(cwd)

    # Add cwd's parent to sys.path so 'pkg_name.models' is importable
    parent = os.path.dirname(cwd)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    # Also add cwd itself for flat imports
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    from askdiana.discovery import discover_models
    models = discover_models(f"{pkg_name}.models")

    if not models:
        # Fallback: try just "models" as a package (if cwd is on sys.path)
        models = discover_models("models")

    return models


def _build_combined_schema(models):
    """Build combined schema from all discovered models."""
    all_tables = []
    for model in models:
        schema = model.to_schema()
        all_tables.extend(schema["tables"])
    return {"tables": all_tables}


def cmd_db(args):
    """Run a db subcommand."""
    subcmd = args.db_command

    if subcmd == "validate":
        _cmd_db_validate()
    elif subcmd == "schema":
        _cmd_db_schema()
    elif subcmd == "push":
        _cmd_db_push(args)
    else:
        print(f"Unknown db command: {subcmd}", file=sys.stderr)
        sys.exit(1)


def _cmd_db_validate():
    """Discover models and validate their schemas locally."""
    models = _discover_local_models()
    if not models:
        print("No models found in models/ directory.")
        print("Make sure you're running this from your extension project root.")
        sys.exit(1)

    schema = _build_combined_schema(models)
    errors = _validate_schema(schema)

    print(f"Found {len(models)} model(s): {', '.join(m.__name__ for m in models)}")
    print()

    for table in schema["tables"]:
        cols = table["columns"]
        print(f"  {table['name']}")
        for col in cols:
            flags = []
            if col.get("primary_key"):
                flags.append("PK")
            if col.get("nullable") is False:
                flags.append("NOT NULL")
            if col.get("max_length"):
                flags.append(f"max={col['max_length']}")
            flag_str = f"  [{', '.join(flags)}]" if flags else ""
            print(f"    {col['name']:30s} {col['type']:10s}{flag_str}")
        print()

    if errors:
        print(f"FAIL  {len(errors)} validation error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("OK  All schemas valid.")


def _cmd_db_schema():
    """Print the JSON schema that would be sent to the backend."""
    models = _discover_local_models()
    if not models:
        print("No models found in models/ directory.")
        sys.exit(1)

    schema = _build_combined_schema(models)
    print(json.dumps(schema, indent=2))


def _cmd_db_push(args):
    """Register and apply schemas via the API."""
    # Load .env from the current directory so developers don't need to export vars
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    install_id = args.install_id or os.environ.get("ASKDIANA_INSTALL_ID", "")
    version = args.version or "1.0.0"
    api_key = os.environ.get("ASKDIANA_API_KEY", "")
    base_url = os.environ.get("ASKDIANA_BASE_URL", "https://app.askdiana.ai")

    if not api_key:
        print("Error: ASKDIANA_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)
    if not install_id:
        print("Error: --install-id is required (or set ASKDIANA_INSTALL_ID).", file=sys.stderr)
        sys.exit(1)

    models = _discover_local_models()
    if not models:
        print("No models found in models/ directory.")
        sys.exit(1)

    # Validate locally first
    schema = _build_combined_schema(models)
    errors = _validate_schema(schema)
    if errors:
        print(f"FAIL  Local validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print(f"Pushing {len(models)} model(s) to {base_url} ...")

    from askdiana.client import AskDianaClient
    client = AskDianaClient(api_key=api_key, base_url=base_url)

    # Register
    try:
        reg = client.register_schema(install_id, version, schema)
        print(f"  Registered: {reg.get('message', 'ok')}")
    except Exception as exc:
        print(f"  FAIL register: {exc}", file=sys.stderr)
        sys.exit(1)

    # Apply each table
    for table in schema["tables"]:
        table_name = table["name"]
        try:
            res = client.apply_schema(install_id, table_name)
            print(f"  Applied: {table_name} -- {res.get('message', 'ok')}")
        except Exception as exc:
            print(f"  FAIL apply {table_name}: {exc}", file=sys.stderr)
            sys.exit(1)

    print("OK  All schemas pushed and applied.")


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #


def _to_class_name(name: str) -> str:
    """Convert 'task_tracker' or 'task' to 'TaskTracker' or 'Task'."""
    return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))


def _write(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _ensure_dir(path: str):
    d = os.path.dirname(path)
    if not os.path.exists(d):
        print(f"Warning: directory '{d}' does not exist. Creating it.", file=sys.stderr)
        os.makedirs(d, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        prog="askdiana",
        description="Ask DIANA Extension SDK CLI",
    )
    sub = parser.add_subparsers(dest="command")

    init_p = sub.add_parser("init", help="Create a new extension project")
    init_p.add_argument("name", help="Extension name (used as directory name)")

    scaffold_p = sub.add_parser("scaffold", help="Generate a model, service, or controller")
    scaffold_p.add_argument("kind", choices=["model", "service", "controller"])
    scaffold_p.add_argument("name", help="Name for the generated file/class")

    db_p = sub.add_parser("db", help="Validate, inspect, or push model schemas")
    db_p.add_argument(
        "db_command",
        choices=["validate", "schema", "push"],
        help="validate: check locally | schema: print JSON | push: register+apply via API",
    )
    db_p.add_argument("--install-id", help="Install UUID (or set ASKDIANA_INSTALL_ID)")
    db_p.add_argument("--version", default="1.0.0", help="Extension version (default: 1.0.0)")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "scaffold":
        cmd_scaffold(args)
    elif args.command == "db":
        cmd_db(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
