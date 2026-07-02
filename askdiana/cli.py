"""
CLI tool for Ask DIANA extensions.

Usage::

    askdiana init my_extension
    askdiana dev --port 5004
    askdiana scaffold model TaskTracker
    askdiana scaffold service task
    askdiana scaffold controller tasks
    askdiana db validate
    askdiana db schema
    askdiana db push --install-id <id> --version 1.0.0
    askdiana deploy
"""

import argparse
import json
import os
import subprocess
import sys

# ------------------------------------------------------------------ #
# Project config (.askdiana.json)                                      #
# ------------------------------------------------------------------ #

_CONFIG_FILE = ".askdiana.json"


def _load_project_config() -> dict:
    """Load .askdiana.json from the current directory. Returns empty dict if missing."""
    config_path = os.path.join(os.getcwd(), _CONFIG_FILE)
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_project_config(config: dict):
    """Write .askdiana.json to the current directory."""
    config_path = os.path.join(os.getcwd(), _CONFIG_FILE)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")

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

APP_TEMPLATE_REACT = '''"""
{name} -- Ask DIANA Extension.
"""

import os
import logging

from dotenv import load_dotenv
load_dotenv()

from flask import send_from_directory
from askdiana import ExtensionApp

logging.basicConfig(level=logging.INFO)

app = ExtensionApp(__name__)

_VIEWS_STATIC = os.path.join(os.path.dirname(__file__), "static")


@app.flask.route("/ui", strict_slashes=False)
def extension_ui():
    return send_from_directory(_VIEWS_STATIC, "index.html")


@app.flask.route("/ui/<path:filename>")
def extension_ui_assets(filename):
    return send_from_directory(_VIEWS_STATIC, filename)


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


MANIFEST_TEMPLATE_SCHEMA = """{
  "name": "%(name)s",
  "slug": "%(slug)s",
  "version": "1.0.0",
  "type": "tool",
  "description": "TODO: describe your extension",
  "short_description": "TODO: short description",
  "permissions": [],
  "pricing": {
    "model": "free"
  },
  "ui": {
    "type": "schema",
    "settings_form": {
      "fields": [
        {
          "name": "api_key",
          "type": "password",
          "label": "API Key",
          "required": false,
          "placeholder": "Enter your API key"
        }
      ]
    }
  }
}
"""

MANIFEST_TEMPLATE_REACT = """{
  "name": "%(name)s",
  "slug": "%(slug)s",
  "version": "1.0.0",
  "type": "tool",
  "description": "TODO: describe your extension",
  "short_description": "TODO: short description",
  "permissions": [],
  "pricing": {
    "model": "free"
  },
  "ui": {
    "type": "iframe",
    "url": "http://localhost:5000/ui",
    "height": "600px",
    "views": { "settings": true, "app": true }
  }
}
"""

VIEWS_PACKAGE_JSON = """{
  "name": "%(slug)s-views",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite build --watch",
    "build": "vite build"
  },
  "dependencies": {
    "askdiana-ui": "file:./askdiana-ui-0.1.0.tgz",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.40",
    "tailwindcss": "^3.4.3",
    "tailwindcss-animate": "^1.0.7",
    "typescript": "^5.4.0",
    "vite": "^5.3.0",
    "vite-plugin-singlefile": "^2.3.3"
  }
}
"""

VIEWS_VITE_CONFIG = """import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    base: env.VITE_BASE_URL ?? "/ui/",
    plugins: [react(), viteSingleFile()],
    build: { outDir: "static", emptyOutDir: true, cssCodeSplit: false },
  };
});
"""

VIEWS_POSTCSS_CONFIG = """export default { plugins: { tailwindcss: {}, autoprefixer: {} } };
"""

VIEWS_TAILWIND_CONFIG = """import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./views/**/*.{ts,tsx}",
    "./node_modules/askdiana-ui/src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
"""

VIEWS_INDEX_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Extension UI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/views/index.tsx"></script>
  </body>
</html>
"""

VIEWS_INDEX_TSX = '''// @ts-ignore: side-effect import of CSS module
import "./tailwind.css";
import React from "react";
import {{ createRoot }} from "react-dom/client";
import {{ bridge, applyTheme, type InitData }} from "askdiana-ui";
import {name}App from "./app";
import {name}Response from "./response";

const params = new URLSearchParams(location.search);
const view = params.get("view") || "app";
const installId = params.get("install_id") || "";

function Root() {{
  const [init, setInit] = React.useState<InitData | null>(null);
  React.useEffect(() => {{
    bridge.ready((data) => {{ applyTheme(data.theme); setInit(data); }});
    const t = setTimeout(
      () => setInit((s) => s ?? ({{ installId, view, config: {{}}, params: {{}} }} as InitData)),
      400,
    );
    return () => clearTimeout(t);
  }}, []);

  if (!init) return <div className="p-4 text-sm text-muted-foreground">Loading...</div>;
  if (view === "response") return <{name}Response init={{init}} installId={{installId}} />;
  return <{name}App init={{init}} installId={{installId}} />;
}}

createRoot(document.getElementById("root")!).render(<Root />);
'''

VIEWS_APP_TSX = '''import React from "react";
import {{ App, type InitData }} from "askdiana-ui";

export default function {name}App({{ init }}: {{ init: InitData; installId: string }}) {{
  return (
    <App bare>
      <div className="space-y-2 p-4">
        <h1 className="text-lg font-semibold">{name}</h1>
        <p className="text-sm text-muted-foreground">Build your extension UI here.</p>
      </div>
    </App>
  );
}}
'''

VIEWS_RESPONSE_TSX = '''import React from "react";
import {{ Response, type InitData }} from "askdiana-ui";

export default function {name}Response({{ init }}: {{ init: InitData; installId: string }}) {{
  const serverBlocks = init.params?.blocks as any[] | undefined;
  if (serverBlocks) return <Response blocks={{serverBlocks}} />;
  return (
    <Response>
      <p className="text-sm">Build your chat response view here.</p>
    </Response>
  );
}}
'''

VIEWS_TSCONFIG = """{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "types": ["node"],
    "strict": true,
    "skipLibCheck": true,
    "noEmit": true
  },
  "include": ["*.ts", "*.tsx", "views/**/*.ts", "views/**/*.tsx"]
}
"""

VIEWS_TAILWIND_CSS = """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-background text-foreground;
  }
}
"""


GITIGNORE_DEFAULT = ".env\n.askdiana.json\n__pycache__/\n*.pyc\n.venv/\n"
GITIGNORE_REACT = GITIGNORE_DEFAULT + "node_modules/\nstatic/\naskdiana-ui-*.tgz\n"


ENV_TEMPLATE = """ASKDIANA_API_KEY=askd_your_key_here
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


def _detect_package_manager() -> str:
    """Return the first package manager found on PATH: pnpm > yarn > bun > npm."""
    import shutil
    for pm in ("pnpm", "yarn", "bun", "npm"):
        if shutil.which(pm):
            return pm
    return "npm"


def cmd_init(args):
    """Create a new extension project directory."""
    name = args.name
    slug = name.lower().replace(" ", "_").replace("-", "_")
    base = os.path.join(os.getcwd(), name)
    ui_mode = args.ui  # "schema" | "react" | None (interactive)

    if os.path.exists(base):
        print(f"Error: directory '{name}' already exists.", file=sys.stderr)
        sys.exit(1)

    # Interactive prompts when --ui flag is omitted
    pm_choice = None
    if ui_mode is None:
        try:
            answer = input(
                "Add React UI components? "
                "(recommended for rich settings/open views) [y/N]: "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = ""
        ui_mode = "react" if answer in ("y", "yes") else "schema"

    if ui_mode == "react" and args.ui is None:
        detected = _detect_package_manager()
        print(f"Which package manager?  1) npm  2) pnpm  3) yarn  4) bun")
        pm_map = {"1": "npm", "2": "pnpm", "3": "yarn", "4": "bun", "": detected}
        try:
            raw = input(f"Choice [{['1','2','3','4'][['npm','pnpm','yarn','bun'].index(detected)]}]: ").strip()
        except (EOFError, KeyboardInterrupt, ValueError):
            raw = ""
        pm_choice = pm_map.get(raw, detected)

    os.makedirs(base, exist_ok=True)

    # `init` writes files only. Folders (models/, services/, controllers/) are
    # created lazily the first time you run `askdiana scaffold ...`, so a fresh
    # project starts minimal instead of carrying empty package directories
    app_template = APP_TEMPLATE_REACT if ui_mode == "react" else APP_TEMPLATE
    manifest_template = MANIFEST_TEMPLATE_REACT if ui_mode == "react" else MANIFEST_TEMPLATE_SCHEMA

    _write(os.path.join(base, "app.py"), app_template.format(name=name))
    _write(os.path.join(base, "manifest.json"), manifest_template % {"name": name, "slug": slug})
    _write(os.path.join(base, ".env.example"), ENV_TEMPLATE)
    _write(os.path.join(base, "requirements.txt"), "askdiana\nflask\npython-dotenv\n")
    _write(os.path.join(base, ".gitignore"), GITIGNORE_REACT if ui_mode == "react" else GITIGNORE_DEFAULT)
    _write(os.path.join(base, ".askdiana.json"), json.dumps({
        "platform_url": "https://app.askdiana.ai",
    }, indent=2) + "\n")

    if ui_mode == "react":
        _scaffold_react_views(base, name, slug)

    print(f"\nCreated extension project: {name}/  (ui: {ui_mode})")
    print(f"  cd {name}")
    print(f"  pip install askdiana[app]")
    print(f"  # Edit .askdiana.json with your platform URL")
    print(f"  # Edit .env with your ASKDIANA_API_KEY")
    print(f"  # Add code: askdiana scaffold model|service|controller <name>")
    if ui_mode == "react":
        if pm_choice:
            # Auto-install Node dependencies
            print(f"\nInstalling Node dependencies with {pm_choice}...")
            result = subprocess.run([pm_choice, "install"], cwd=base)
            if result.returncode == 0:
                print(f"  Done — run `cd {name} && {pm_choice} run build` to build the UI.")
            else:
                print(
                    f"  Note: {pm_choice} install failed — run it manually: "
                    f"cd {name} && {pm_choice} install && {pm_choice} run build",
                    file=sys.stderr,
                )
        else:
            print(f"  # Build the UI: npm install && npm run build")
        print(f"  # (settings_form in manifest.json is not used in react mode —")
        print(f"  #  customize views/app.tsx / views/response.tsx instead)")
    else:
        print(f"  # Customize manifest.json's \"ui.settings_form.fields\" — the host")
        print(f"  #  renders the settings form for you, no frontend code needed")
    print(f"  askdiana dev --port 5000")


_RELAY_TIMEOUT = 600  # seconds — must match CHAT_RESPOND_TIMEOUT/INVOKE_TIMEOUT on backend


def _relay_loop(platform_url: str, api_key: str, port: int, verify_ssl: bool):
    """Background thread: long-poll the platform relay and forward requests to local Flask."""
    import time
    import requests as _req
    
    session = _req.Session()
    session.verify = verify_ssl

    poll_url = f"{platform_url.rstrip('/')}/api/ext/relay/poll"
    respond_base = f"{platform_url.rstrip('/')}/api/ext/relay/respond"
    local_base = f"http://localhost:{port}"
    headers = {"X-API-Key": api_key}

    while True:
        try:
            resp = session.get(
                poll_url,
                headers=headers,
                params={"timeout": 30},
                timeout=35,
            )
            if resp.status_code != 200:
                time.sleep(2)
                continue

            incoming = resp.json().get("request")
            if not incoming:
                continue  # poll timed out with no request, loop immediately

            request_id = incoming["request_id"]
            method = incoming.get("method", "POST")
            path = incoming.get("path", "/api/chat")
            body = incoming.get("body", {})

            try:
                local_resp = _req.request(
                    method=method,
                    url=f"{local_base}{path}",
                    json=body,
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=_RELAY_TIMEOUT,
                )
                resp_body = local_resp.json()
                status = local_resp.status_code
            except Exception as e:
                resp_body = {"error": str(e)}
                status = 502

            session.post(f"{respond_base}/{request_id}", json={"status": status, "body": resp_body}, headers=headers, timeout=10)

        except Exception:
            time.sleep(2)


def _relay_ws_loop(platform_url: str, api_key: str, port: int, verify_ssl: bool) -> bool:
    """Hold one WS connection open; forward pushed requests to local Flask, push
    responses back. Returns False immediately if the initial connection fails, so
    the caller can fall back to _relay_loop."""
    import json as _json
    import threading
    import requests as _req
    import websocket

    ws_scheme = "wss" if platform_url.startswith("https://") else "ws"
    host = platform_url.split("://", 1)[1].rstrip("/")
    ws_url = f"{ws_scheme}://{host}/api/ext/relay/ws"
    local_base = f"http://localhost:{port}"

    def on_message(ws, message):
        try:
            incoming = _json.loads(message)
        except Exception:
            return
        if incoming.get("type") != "request":
            return
        request_id = incoming["request_id"]
        try:
            local_resp = _req.request(
                method=incoming.get("method", "POST"),
                url=f"{local_base}{incoming.get('path', '/api/chat')}",
                json=incoming.get("body", {}),
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=_RELAY_TIMEOUT,
            )
            resp_body, status = local_resp.json(), local_resp.status_code
        except Exception as e:
            resp_body, status = {"error": str(e)}, 502
        ws.send(_json.dumps({"type": "response", "request_id": request_id, "body": resp_body, "status": status}))

    def on_error(ws, error):
        print(f"  Relay WS error: {error}", file=sys.stderr)

    connected = threading.Event()

    def on_open(ws):
        connected.set()

    app = websocket.WebSocketApp(
        ws_url, header=[f"X-API-Key: {api_key}"],
        on_message=on_message, on_error=on_error, on_open=on_open,
    )
    t = threading.Thread(
        target=app.run_forever,
        kwargs={"sslopt": {"cert_reqs": 0} if not verify_ssl else None, "ping_interval": 25},
        daemon=True,
    )
    t.start()
    return connected.wait(timeout=5)  # False => caller falls back to HTTP relay


def _start_relay(platform_url: str, api_key: str, port: int, verify_ssl: bool):
    import threading

    try:
        if _relay_ws_loop(platform_url, api_key, port, verify_ssl):
            print("  Relay active (WebSocket) — requests will be forwarded to your local server.")
            return
    except Exception as e:
        print(f"  WS relay unavailable ({e}), falling back to HTTP poll relay.", file=sys.stderr)

    print("  Relay active (HTTP poll) — requests from the platform will be forwarded to your local server.")
    t = threading.Thread(target=_relay_loop, args=(platform_url, api_key, port, verify_ssl), daemon=True)
    t.start()


def cmd_dev(args):
    """Start the extension in dev mode: register with platform + run Flask.

    Only requires ASKDIANA_API_KEY in .env and platform_url in .askdiana.json.
    The API key identifies the developer and extension — no extension_id or
    version_id needed.
    """
    # Load .env first so PORT (and other vars) are available below.
    env_path = os.path.join(os.getcwd(), ".env")
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
    except ImportError:
        pass

    # Port precedence: explicit --port flag > PORT in .env > 5000 default.
    port = args.port if args.port is not None else int(os.environ.get("PORT", 5000))

    # Load project config (only needs platform_url)
    config = _load_project_config()
    platform_url = config.get("platform_url", "")

    api_key = os.environ.get("ASKDIANA_API_KEY", "")
    # Check both env var and .askdiana.json for verify_ssl
    verify_ssl_env = os.environ.get("ASKDIANA_VERIFY_SSL", "").lower()
    verify_ssl_config = str(config.get("verify_ssl", "")).lower()
    if verify_ssl_env in ("false", "0", "no") or verify_ssl_config in ("false", "0", "no"):
        verify_ssl = False
    else:
        verify_ssl = True

    if not api_key:
        print("Error: ASKDIANA_API_KEY is required in .env", file=sys.stderr)
        sys.exit(1)
    if not platform_url:
        print(f"Error: platform_url is required in {_CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)

    # Disable SSL warnings if needed
    if not verify_ssl:
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except ImportError:
            pass

    # Load manifest.json to send along with registration
    manifest = None
    manifest_path = os.path.join(os.getcwd(), "manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
        except Exception as e:
            print(f"  Warning: could not read manifest.json: {e}", file=sys.stderr)

    if manifest and isinstance(manifest.get("ui"), dict) and manifest["ui"].get("type") == "iframe":
        # Accept either views/static/index.html (standard scaffold) or
        # static/index.html (extensions that build directly to the project root).
        views_static = os.path.join(os.getcwd(), "views", "static", "index.html")
        root_static  = os.path.join(os.getcwd(), "static", "index.html")
        if not os.path.exists(views_static) and not os.path.exists(root_static):
            print(
                "  Note: static/index.html not found — run "
                "`npm run build` (or `pnpm run build`) "
                "before opening the UI.",
                file=sys.stderr,
            )

    # Register with platform — use tunnel URL from config if set, else localhost (relay mode)
    webhook_url = config.get("webhook_url") or f"http://localhost:{port}"
    register_url = f"{platform_url.rstrip('/')}/api/ext/register"

    print(f"Registering {webhook_url} with {platform_url}...")

    try:
        import requests
        register_payload = {"webhook_url": webhook_url}
        if manifest:
            register_payload["manifest"] = manifest
        resp = requests.post(
            register_url,
            json=register_payload,
            headers={"X-API-Key": api_key},
            timeout=15,
            verify=verify_ssl,
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"  Registered! version_id={data.get('version_id', 'unknown')}")
            _start_relay(platform_url, api_key, port, verify_ssl)
        else:
            print(f"  Warning: registration failed ({resp.status_code}): {resp.text[:200]}", file=sys.stderr)
            print("  Continuing anyway — the extension will start but may not receive requests.", file=sys.stderr)
    except Exception as e:
        print(f"  Warning: could not reach platform: {e}", file=sys.stderr)
        print("  Continuing anyway — the extension will start but may not receive requests.", file=sys.stderr)

    # Start the Flask app
    print(f"\nStarting extension on port {port}...")
    app_file = os.path.join(os.getcwd(), "app.py")
    if not os.path.exists(app_file):
        print(f"Error: app.py not found in {os.getcwd()}", file=sys.stderr)
        sys.exit(1)

    env = os.environ.copy()
    env["PORT"] = str(port)
    if platform_url and not env.get("ASKDIANA_BASE_URL"):
        env["ASKDIANA_BASE_URL"] = platform_url.rstrip("/")
    if not verify_ssl:
        env["ASKDIANA_VERIFY_SSL"] = "false"
    try:
        subprocess.run([sys.executable, "app.py"], env=env)
    except KeyboardInterrupt:
        print("\nExtension stopped.")


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


def _scaffold_react_views(base: str, name: str, slug: str):
    """Write a minimal askdiana-ui-based React project (files at root, sources in views/)."""
    import shutil

    views = os.path.join(base, "views")
    os.makedirs(views, exist_ok=True)

    # Copy bundled askdiana-ui tarball so pnpm/npm can install it offline
    _data_dir = os.path.join(os.path.dirname(__file__), "data")
    _tgz_name = "askdiana-ui-0.1.0.tgz"
    _tgz_src = os.path.join(_data_dir, _tgz_name)
    if os.path.exists(_tgz_src):
        shutil.copy2(_tgz_src, os.path.join(base, _tgz_name))

    # Root-level build tooling
    _write(os.path.join(base, "package.json"), VIEWS_PACKAGE_JSON % {"slug": slug})
    _write(os.path.join(base, "vite.config.ts"), VIEWS_VITE_CONFIG)
    _write(os.path.join(base, "index.html"), VIEWS_INDEX_HTML)
    _write(os.path.join(base, "postcss.config.js"), VIEWS_POSTCSS_CONFIG)
    _write(os.path.join(base, "tailwind.config.ts"), VIEWS_TAILWIND_CONFIG)
    _write(os.path.join(base, "tsconfig.json"), VIEWS_TSCONFIG)

    # React source files in views/
    _write(os.path.join(views, "index.tsx"), VIEWS_INDEX_TSX.format(name=name))
    _write(os.path.join(views, "app.tsx"), VIEWS_APP_TSX.format(name=name))
    _write(os.path.join(views, "response.tsx"), VIEWS_RESPONSE_TSX.format(name=name))
    _write(os.path.join(views, "tailwind.css"), VIEWS_TAILWIND_CSS)



def _scaffold_model(name: str):
    class_name = _to_class_name(name)
    table_name = name.lower().replace(" ", "_")

    _ensure_package("models", MODELS_INIT)
    path = os.path.join(os.getcwd(), "models", f"{table_name}.py")
    if _exists_guard(path):
        return
    _write(path, MODEL_TEMPLATE.format(class_name=class_name, table_name=table_name))
    print(f"Created model: models/{table_name}.py ({class_name})")


def _scaffold_service(name: str):
    class_name = _to_class_name(name)
    slug = name.lower().replace(" ", "_")

    _ensure_package("services", SERVICES_INIT)
    path = os.path.join(os.getcwd(), "services", f"{slug}_service.py")
    if _exists_guard(path):
        return
    _write(path, SERVICE_TEMPLATE.format(class_name=class_name, name=name))
    print(f"Created service: services/{slug}_service.py ({class_name}Service)")


def _scaffold_controller(name: str):
    slug = name.lower().replace(" ", "_")
    bp_var = f"{slug}_bp"

    _ensure_package("controllers", CONTROLLERS_INIT)
    path = os.path.join(os.getcwd(), "controllers", f"{slug}.py")
    if _exists_guard(path):
        return
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
    env_path = os.path.join(os.getcwd(), ".env")
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
    except ImportError:
        print("Warning: python-dotenv not installed. Install it or export env vars manually.", file=sys.stderr)
    config = _load_project_config()
    install_id = args.install_id or os.environ.get("ASKDIANA_INSTALL_ID", "")
    version = args.version or "1.0.0"
    api_key = os.environ.get("ASKDIANA_API_KEY", "")
    base_url = config.get("platform_url", "")

    if not api_key:
        print("Error: ASKDIANA_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)
    if not base_url:
        print(f"Error: platform_url is required in {_CONFIG_FILE}", file=sys.stderr)
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


def _ensure_package(dir_name: str, init_content: str = ""):
    """Create <cwd>/<dir_name>/ as a Python package if it doesn't exist yet.

    Used by the scaffold commands so folders are created lazily (init no longer
    makes them). An existing folder is left as-is; we only add __init__.py when
    it's missing.
    """
    d = os.path.join(os.getcwd(), dir_name)
    is_new = not os.path.isdir(d)
    os.makedirs(d, exist_ok=True)
    init_path = os.path.join(d, "__init__.py")
    if not os.path.exists(init_path):
        _write(init_path, init_content)
    if is_new:
        print(f"Created {dir_name}/ package")


def _exists_guard(path: str) -> bool:
    """Return True (and warn) if *path* already exists, so callers can skip it
    instead of silently overwriting the developer's file."""
    if os.path.exists(path):
        rel = os.path.relpath(path, os.getcwd())
        print(f"Skipped: {rel} already exists.", file=sys.stderr)
        return True
    return False


# ------------------------------------------------------------------ #
# Package & Deploy commands                                            #
# ------------------------------------------------------------------ #

# Files and directories to exclude from the package
_PACKAGE_EXCLUDES = {
    ".env", ".env.local", ".env.production", ".env.development",
    ".askdiana.json",
    "__pycache__", ".git", ".venv", "venv", "env",
    "node_modules", ".mypy_cache", ".pytest_cache",
    ".DS_Store", "Thumbs.db",
}

# SDK/platform env vars stripped from .env before packaging
_ENV_STRIP_PREFIXES = (
    "ASKDIANA_UPLOAD_URL",
    "ASKDIANA_EXTENSION_ID", "ASKDIANA_VERSION_ID", "ASKDIANA_VERIFY_SSL",
    "ASKDIANA_INSTALL_ID",
)


def _sanitize_env_file(src_path: str, dest_path: str):
    """Copy .env but strip SDK/platform credentials — keep only runtime vars."""
    with open(src_path, "r") as f:
        lines = f.readlines()
    with open(dest_path, "w") as f:
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                key = stripped.split("=", 1)[0].strip()
                if key.startswith(_ENV_STRIP_PREFIXES):
                    continue
            f.write(line)


def cmd_package(args):
    """Create a deployable zip package from the current extension project."""
    cwd = os.getcwd()

    # Validate required files
    required = ["app.py", "requirements.txt", "manifest.json"]
    missing = [f for f in required if not os.path.exists(os.path.join(cwd, f))]
    if missing:
        print(f"Error: missing required files: {', '.join(missing)}", file=sys.stderr)
        print("Make sure you're running this from your extension project root.")
        sys.exit(1)

    # Read manifest for slug and version
    try:
        with open(os.path.join(cwd, "manifest.json"), "r") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"Error reading manifest.json: {e}", file=sys.stderr)
        sys.exit(1)

    slug = manifest.get("slug", os.path.basename(cwd))
    version = manifest.get("version", "1.0.0")
    output_name = args.output or f"extension-{slug}-{version}.zip"

    import zipfile as _zf

    file_count = 0
    with _zf.ZipFile(output_name, "w", _zf.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(cwd):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in _PACKAGE_EXCLUDES]
            for fname in files:
                if fname in _PACKAGE_EXCLUDES or fname.startswith(".env"):
                    continue
                if fname.endswith((".pyc", ".pyo")):
                    continue
                full_path = os.path.join(root, fname)
                arc_name = os.path.relpath(full_path, cwd)
                zf.write(full_path, arc_name)
                file_count += 1

    size_kb = os.path.getsize(output_name) / 1024
    print(f"Package created: {output_name}")
    print(f"  Files: {file_count}")
    print(f"  Size: {size_kb:.1f} KB")
    print(f"  Slug: {slug}")
    print(f"  Version: {version}")


def cmd_deploy(args):
    """Package and upload to Ask DIANA for platform-hosted deployment.

    Only requires ASKDIANA_API_KEY in .env and platform_url in .askdiana.json.
    The extension is identified by the slug + version in manifest.json.
    No extension_id or version_id needed.
    """
    # Load .env from the current working directory
    env_path = os.path.join(os.getcwd(), ".env")
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
    except ImportError:
        print("Warning: python-dotenv not installed. Install it or export env vars manually.", file=sys.stderr)

    config = _load_project_config()
    api_key = os.environ.get("ASKDIANA_API_KEY", "")
    base_url = config.get("platform_url", "") or os.environ.get("ASKDIANA_UPLOAD_URL", "")
    # Check both env var and .askdiana.json for verify_ssl
    _vs_env = os.environ.get("ASKDIANA_VERIFY_SSL", "").lower()
    _vs_cfg = str(config.get("verify_ssl", "")).lower()
    verify_ssl = not (_vs_env in ("false", "0", "no") or _vs_cfg in ("false", "0", "no"))

    if not api_key:
        print("Error: ASKDIANA_API_KEY is required in .env", file=sys.stderr)
        sys.exit(1)
    if not base_url:
        print(f"Error: platform_url is required in {_CONFIG_FILE}", file=sys.stderr)
        sys.exit(1)

    # Package first
    cwd = os.getcwd()
    required = ["app.py", "requirements.txt", "manifest.json"]
    missing = [f for f in required if not os.path.exists(os.path.join(cwd, f))]
    if missing:
        print(f"Error: missing required files: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(os.path.join(cwd, "manifest.json"), "r") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"Error reading manifest.json: {e}", file=sys.stderr)
        sys.exit(1)

    slug = manifest.get("slug", os.path.basename(cwd))
    version = manifest.get("version", "1.0.0")
    package_name = f"extension-{slug}-{version}.zip"

    import zipfile as _zf

    print(f"Packaging {slug} v{version}...")
    with _zf.ZipFile(package_name, "w", _zf.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(cwd):
            dirs[:] = [d for d in dirs if d not in _PACKAGE_EXCLUDES]
            for fname in files:
                if fname in _PACKAGE_EXCLUDES or fname.startswith(".env") or fname.endswith((".pyc", ".pyo")):
                    continue
                full_path = os.path.join(root, fname)
                arc_name = os.path.relpath(full_path, cwd)
                zf.write(full_path, arc_name)

    # Upload via /api/marketplace/deploy (resolved by API key + manifest slug/version)
    import requests

    url = f"{base_url.rstrip('/')}/api/marketplace/deploy"
    print(f"Uploading to {base_url}...")

    with open(package_name, "rb") as f:
        resp = requests.post(
            url,
            headers={"X-API-Key": api_key},
            files={"file": (package_name, f, "application/zip")},
            timeout=120,
            verify=verify_ssl,
        )

    # Clean up local package
    try:
        os.remove(package_name)
    except Exception:
        pass

    if resp.status_code == 200:
        data = resp.json()
        print(f"Upload successful!")
        print(f"  Deployment type: platform_hosted")
        print(f"  Status: {data.get('version', {}).get('status', 'unknown')}")
        print()
        print("Next steps:")
        print("  1. An admin will review your code for security")
        print("  2. Once approved, the admin will deploy your extension")
        print("  3. Your extension will be available in the marketplace")
    else:
        print(f"Upload failed ({resp.status_code}):", file=sys.stderr)
        try:
            print(f"  {resp.json().get('message', resp.text)}", file=sys.stderr)
        except Exception:
            print(f"  {resp.text}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="askdiana",
        description="Ask DIANA Extension SDK CLI",
    )
    sub = parser.add_subparsers(dest="command")

    init_p = sub.add_parser("init", help="Create a new extension project")
    init_p.add_argument("name", help="Extension name (used as directory name)")
    init_p.add_argument(
        "--ui",
        choices=["schema", "react"],
        default=None,
        help=(
            "How the extension's settings/app UI is built: "
            "'schema' = host renders a form from manifest.json (no frontend code), "
            "'react' = bring your own UI with askdiana-ui + a bundled views/ folder (needs Node). "
            "Omit to be prompted interactively."
        ),
    )

    dev_p = sub.add_parser("dev", help="Register with platform and start local dev server")
    dev_p.add_argument("--port", type=int, default=None, help="Port to run on (default: $PORT from .env, else 5000)")

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

    pkg_p = sub.add_parser("package", help="Create a deployable zip package")
    pkg_p.add_argument("-o", "--output", help="Output filename (default: extension-<slug>-<version>.zip)")

    sub.add_parser("deploy", help="Package and upload for platform-hosted deployment")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args)
    elif args.command == "dev":
        cmd_dev(args)
    elif args.command == "scaffold":
        cmd_scaffold(args)
    elif args.command == "db":
        cmd_db(args)
    elif args.command == "package":
        cmd_package(args)
    elif args.command == "deploy":
        cmd_deploy(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
