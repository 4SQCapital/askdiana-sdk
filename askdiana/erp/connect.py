from __future__ import annotations

from collections.abc import Mapping
from html import escape

from flask import Blueprint, Response, redirect, request

from . import constants as C
from .connector import ErpConnector
from .errors import ErpError
from .pack import CredentialSpec, Pack

FORM_INSTALL_ID, FORM_NONCE, FORM_METHOD = "install_id", "nonce", "method"
_INPUT_TYPES = {C.INPUT_TEXT: "text", C.INPUT_URL: "url", C.INPUT_SECRET: "password"}
_PAGE_HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}
_CSS = (
    "body{font-family:system-ui,sans-serif;background:#f6f6f7;color:#1b1b1f;margin:0}"
    "main{max-width:440px;margin:32px auto;padding:0 16px}"
    "form,.oauth{background:#fff;border:1px solid #dcdce0;border-radius:8px;padding:16px;margin:16px 0}"
    "h1{font-size:20px}h2{font-size:16px;margin:0 0 8px}"
    "label{display:block;margin:12px 0;font-size:14px}"
    "input{display:block;width:100%;box-sizing:border-box;padding:8px;margin-top:4px;"
    "border:1px solid #b8b8c0;border-radius:6px;font:inherit}"
    "small{display:block;color:#5c5c66;margin-top:4px}"
    "button,.button{display:inline-block;background:#1b1b1f;color:#fff;border:0;border-radius:6px;"
    "padding:10px 16px;font:inherit;text-decoration:none;cursor:pointer}"
    ".error{color:#b3261e;background:#fdecea;border-radius:6px;padding:8px 12px}"
)


def connect_blueprint(pack: Pack, connector: ErpConnector) -> Blueprint:
    bp = Blueprint("erp_connect", __name__)

    def render_page(install_id: str, nonce: str, *, error: str | None = None, status: int = 200,
                    previous: Mapping[str, str] | None = None) -> Response:
        try:
            redirect_uri = connector.check_nonce(install_id, nonce)
        except ErpError as exc:
            return _page(pack, error=exc.message, status=exc.http_status)
        oauth_url = connector.oauth.auth_url(install_id, redirect_uri) if connector.oauth else None
        return _page(pack, install_id=install_id, nonce=nonce, oauth_url=oauth_url,
                     error=error, status=status, previous=previous or {})

    @bp.route(C.CONNECT_PAGE_PATH, methods=["GET"])
    def connect_page():
        return render_page(request.args.get(FORM_INSTALL_ID, ""), request.args.get(FORM_NONCE, ""))

    @bp.route(C.CONNECT_API_PATH, methods=["POST"])
    def connect_submit():
        form = request.form
        install_id, nonce = form.get(FORM_INSTALL_ID, ""), form.get(FORM_NONCE, "")
        try:
            next_url = connector.connect_with_credentials(install_id, nonce, form.get(FORM_METHOD, ""), form)
        except ErpError as exc:
            return render_page(install_id, nonce, error=exc.message, status=exc.http_status, previous=form)
        return redirect(next_url, code=303)

    return bp


def _page(pack: Pack, *, install_id: str = "", nonce: str = "", oauth_url: str | None = None,
          error: str | None = None, status: int = 200, previous: Mapping[str, str] | None = None) -> Response:
    title = f"Connect {pack.label}"
    parts = [f"<h1>{escape(title)}</h1>"]
    if error:
        parts.append(f'<p class="error" role="alert">{escape(error)}</p>')
    if install_id:
        if oauth_url:
            button = escape(pack.auth.oauth2.label)
            parts.append(f'<div class="oauth"><a class="button" href="{escape(oauth_url)}">{button}</a></div>')
        for spec in pack.auth.credentials.values():
            parts.append(_form(spec, install_id, nonce, previous or {}))
    html = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(title)}</title><style>{_CSS}</style></head>"
        f"<body><main>{''.join(parts)}</main></body></html>"
    )
    return Response(html, status=status, headers=_PAGE_HEADERS, mimetype="text/html")


def _form(spec: CredentialSpec, install_id: str, nonce: str, previous: Mapping[str, str]) -> str:
    same_method = previous.get(FORM_METHOD) == spec.method
    rows = []
    for item in spec.inputs:
        keep = same_method and item.kind != C.INPUT_SECRET
        value = previous.get(item.name, "") if keep else (item.default or "")
        required = " required" if item.required else ""
        help_text = f"<small>{escape(item.help)}</small>" if item.help else ""
        rows.append(
            f'<label>{escape(item.label)}<input name="{escape(item.name)}" type="{_INPUT_TYPES[item.kind]}" '
            f'value="{escape(value)}" autocomplete="off"{required}>{help_text}</label>'
        )
    hidden = "".join(
        f'<input type="hidden" name="{name}" value="{escape(value)}">'
        for name, value in ((FORM_INSTALL_ID, install_id), (FORM_NONCE, nonce), (FORM_METHOD, spec.method))
    )
    action = C.CONNECT_API_PATH.lstrip("/")
    return (f'<form method="post" action="{action}"><h2>{escape(spec.label)}</h2>{hidden}'
            f'{"".join(rows)}<button type="submit">Connect</button></form>')
