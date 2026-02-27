"""
Application wrapper for structured Ask DIANA extensions.

``ExtensionApp`` wraps Flask and provides auto-discovery of models and
controllers, built-in health endpoint, webhook verification, and
client initialisation from environment variables.

Usage::

    from askdiana import ExtensionApp

    app = ExtensionApp(__name__)

    if __name__ == "__main__":
        app.run(port=5000)
"""

import inspect
import logging
import os
from typing import Any, Dict, List, Optional, Type

from flask import Flask, jsonify, request

from .client import AskDianaClient
from .discovery import discover_blueprints, discover_models
from .models import ExtModel, register_all_models
from .webhooks import WebhookVerificationError, verify_webhook

logger = logging.getLogger(__name__)


class ExtensionApp:
    """Wrapper around Flask for structured extensions.

    Features:
    - ``AskDianaClient`` initialised from env vars or explicit params
    - Auto-discovery of ``ExtModel`` subclasses from a ``models/`` package
    - Auto-discovery and registration of Flask Blueprints from ``controllers/``
    - Built-in ``/health`` endpoint
    - ``setup_models()`` to register + apply all discovered models
    """

    def __init__(
        self,
        import_name: str,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        auto_discover: bool = True,
        models_package: Optional[str] = None,
        controllers_package: Optional[str] = None,
        **flask_kwargs: Any,
    ):
        """
        Args:
            import_name: Passed to Flask (usually ``__name__``).
            api_key: Override ``ASKDIANA_API_KEY`` env var.
            base_url: Override ``ASKDIANA_BASE_URL`` env var.
            webhook_secret: Override ``WEBHOOK_SIGNING_SECRET`` env var.
            auto_discover: Scan ``models/`` and ``controllers/`` packages.
            models_package: Dotted path to models package.
            controllers_package: Dotted path to controllers package.
            **flask_kwargs: Extra keyword arguments forwarded to ``Flask()``.
        """
        # --- Flask app ---
        # If Flask can't resolve the root path (e.g. namespace package),
        # fall back to cwd.
        try:
            self.flask = Flask(import_name, **flask_kwargs)
        except RuntimeError:
            self.flask = Flask(
                import_name,
                root_path=os.getcwd(),
                **flask_kwargs,
            )
        self.flask.config["ext_app"] = self

        # --- SDK client ---
        self._api_key = api_key or os.environ.get("ASKDIANA_API_KEY", "")
        self._base_url = base_url or os.environ.get("ASKDIANA_BASE_URL", "https://app.askdiana.ai")
        self._webhook_secret = webhook_secret or os.environ.get("WEBHOOK_SIGNING_SECRET", "")

        self.client: Optional[AskDianaClient] = None
        if self._api_key:
            self.client = AskDianaClient(api_key=self._api_key, base_url=self._base_url)

        # --- Registries ---
        self._models: List[Type[ExtModel]] = []

        # --- Built-in routes ---
        self._register_health()

        # --- Auto-discovery ---
        if auto_discover:
            base_pkg = self._resolve_base_package(import_name)
            mp = models_package or f"{base_pkg}.models"
            cp = controllers_package or f"{base_pkg}.controllers"

            # Ensure the parent of the extension directory is on sys.path
            # so dotted imports like "notes_app.controllers" work even when
            # running `python app.py` from inside the package directory.
            import sys as _sys
            _cwd = os.getcwd()
            _parent = os.path.dirname(_cwd)
            if _parent and _parent not in _sys.path:
                _sys.path.insert(0, _parent)
            if _cwd not in _sys.path:
                _sys.path.insert(0, _cwd)

            self._models = discover_models(mp)
            for bp in discover_blueprints(cp):
                self.flask.register_blueprint(bp)

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    def verify_request(self) -> None:
        """Verify the current Flask request's webhook signature.

        Raises:
            WebhookVerificationError: If verification fails.
        """
        verify_webhook(
            request_body=request.get_data(),
            signature_header=request.headers.get("X-AskDiana-Signature", ""),
            secret=self._webhook_secret,
            timestamp_header=request.headers.get("X-AskDiana-Delivery-Timestamp"),
        )

    @property
    def models(self) -> List[Type[ExtModel]]:
        """All discovered ExtModel subclasses."""
        return list(self._models)

    def register_model(self, model: Type[ExtModel]) -> None:
        """Manually register an ExtModel subclass."""
        if model not in self._models:
            self._models.append(model)

    def register_blueprint(self, blueprint, **kwargs) -> None:
        """Register a Flask Blueprint on the underlying app."""
        self.flask.register_blueprint(blueprint, **kwargs)

    def setup_models(self, install_id: str, version: str) -> Dict[str, Any]:
        """Register and apply all discovered models for a given install.

        Args:
            install_id: The install UUID from the webhook payload.
            version: Extension version string (e.g. ``"1.0.0"``).

        Returns:
            Dict with ``"registered"`` and ``"applied"`` results.
        """
        if not self.client:
            raise RuntimeError(
                "AskDianaClient not initialised. "
                "Set ASKDIANA_API_KEY or pass api_key= to ExtensionApp."
            )
        if not self._models:
            return {"registered": None, "applied": []}

        reg_result = register_all_models(self.client, install_id, version, *self._models)

        apply_results = []
        for model in self._models:
            result = model.apply(self.client, install_id)
            apply_results.append(result)

        return {"registered": reg_result, "applied": apply_results}

    def run(self, host: str = "0.0.0.0", port: int = 5000, **kwargs):
        """Run the Flask development server."""
        self.flask.run(host=host, port=port, **kwargs)

    # ------------------------------------------------------------------ #
    # WSGI compatibility                                                   #
    # ------------------------------------------------------------------ #

    def __call__(self, environ, start_response):
        """WSGI entry point — delegates to the Flask app."""
        return self.flask(environ, start_response)

    # ------------------------------------------------------------------ #
    # Internals                                                            #
    # ------------------------------------------------------------------ #

    def _register_health(self):
        @self.flask.route("/health", methods=["GET"])
        def _health():
            return jsonify({"status": "ok"}), 200

    @staticmethod
    def _resolve_base_package(import_name: str) -> str:
        """Derive the base package name for auto-discovery.

        If *import_name* is ``"__main__"``, inspects the call stack to
        find the parent directory name.
        """
        if import_name != "__main__":
            parts = import_name.rsplit(".", 1)
            return parts[0] if len(parts) > 1 else import_name

        # Fallback: use the parent directory of the caller's file
        frame = inspect.stack()[2]
        caller_file = frame.filename
        return os.path.basename(os.path.dirname(os.path.abspath(caller_file)))
