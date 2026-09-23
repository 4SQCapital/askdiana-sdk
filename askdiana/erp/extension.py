from __future__ import annotations

from pathlib import Path

from flask import Blueprint, jsonify, request, send_from_directory

from . import constants as C
from .chat import ErpChatService
from .connect import connect_blueprint
from .connector import ErpConnector
from .dashboard import build_tab, entities_for_tab, tab_index
from .errors import ErpError
from .llm import LLMClient, llm_from_env
from .pack import Pack, load_pack
from .pipeline import AnswerPipeline
from .source import DataSource, DemoProvider
from .transport import DirectTransport

INSTALL_ID_PARAM = "install_id"
TAB_PARAM = "tab"
CORS_HEADERS = {
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, ngrok-skip-browser-warning",
    "ngrok-skip-browser-warning": "1",
}


class ErpExtension:
    def __init__(self, pack_path: str | Path, *, demo_provider: DemoProvider | None = None,
                static_dir: str | Path | None = None, llm: LLMClient | None = None):
        self.pack: Pack = load_pack(str(pack_path))
        self._demo_provider = demo_provider
        self._static_dir = Path(static_dir) if static_dir else None
        self._llm = llm
        self.connector: ErpConnector | None = None
        self.source: DataSource | None = None
        self.pipeline: AnswerPipeline | None = None

    def mount(self, app) -> "ErpExtension":
        self.connector = ErpConnector(app.client, self.pack)
        self.source = DataSource(self.pack, self.connector, DirectTransport(self.connector, self.pack),
                                demo_provider=self._demo_provider)
        self.pipeline = AnswerPipeline(self.pack, self.source, self._llm or llm_from_env())

        self.connector.register_routes(app)
        ErpChatService(app.client, self.pack, self.pipeline).register_routes(app)
        if self.pack.auth.credentials:
            app.register_blueprint(connect_blueprint(self.pack, self.connector))
        app.register_blueprint(data_blueprint(self.pack, self.source))
        if self._static_dir:
            _register_ui(app.flask, self._static_dir)
        _register_webhooks(app, self.source)
        _register_cors(app.flask)
        return self


def data_blueprint(pack: Pack, source: DataSource) -> Blueprint:
    bp = Blueprint("erp_data", __name__)

    @bp.errorhandler(ErpError)
    def _erp_error(exc: ErpError):
        return jsonify(exc.to_dict()), exc.http_status

    @bp.route("/api/meta", methods=["GET", "OPTIONS"])
    def meta():
        mode = source.mode(request.args.get(INSTALL_ID_PARAM))
        return jsonify({"live": mode == C.MODE_LIVE, "mode": mode, "label": pack.label})

    @bp.route("/api/dashboard", methods=["GET", "OPTIONS"])
    def dashboard():
        install_id = request.args.get(INSTALL_ID_PARAM)
        tab = pack.tab(request.args.get(TAB_PARAM) or pack.tabs[0].id)
        data, _ = source.fetch_many(install_id, entities_for_tab(pack, tab))
        return jsonify({"mode": source.mode(install_id), "tabs": tab_index(pack), "tab": build_tab(pack, tab, data)})

    @bp.route("/api/<entity>", methods=["GET", "OPTIONS"])
    def rows(entity: str):
        result = source.fetch(request.args.get(INSTALL_ID_PARAM), entity)
        return jsonify({"items": result.rows, "count": len(result.rows), "truncated": result.truncated})

    return bp


def _register_ui(flask_app, static_dir: Path) -> None:
    @flask_app.route("/ui", strict_slashes=False)
    def extension_ui():
        return send_from_directory(static_dir, "index.html")

    @flask_app.route("/ui/<path:filename>")
    def extension_ui_assets(filename):
        return send_from_directory(static_dir, filename)


def _register_webhooks(app, source: DataSource) -> None:
    @app.flask.route("/webhooks/install", methods=["POST"])
    def on_install():
        app.verify_request()
        if app.models:
            app.setup_models(request.get_json()["data"]["install_id"], version="1.0.0")
        return jsonify({"ok": True}), 200

    @app.flask.route("/webhooks/uninstall", methods=["POST"])
    def on_uninstall():
        app.verify_request()
        source.invalidate((request.get_json() or {}).get("data", {}).get("install_id", ""))
        return jsonify({"ok": True}), 200


def _register_cors(flask_app) -> None:
    @flask_app.after_request
    def add_headers(response):
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "") or "*"
        response.headers.update(CORS_HEADERS)
        return response
