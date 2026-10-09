from __future__ import annotations

from collections.abc import Mapping
from html import escape

from flask import Blueprint, Response, jsonify, redirect, request

from . import constants as C
from .connection import connect_options, deployment_groups
from .connector import ErpConnector
from .errors import ErpError
from .pack import CredentialSpec, Pack

FORM_INSTALL_ID, FORM_NONCE, FORM_METHOD = "install_id", "nonce", "method"
_INPUT_TYPES = {C.INPUT_TEXT: "text", C.INPUT_URL: "url", C.INPUT_SECRET: "password"}
_ACTION = C.CONNECT_API_PATH.lstrip("/")
_PAGE_HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}
_BASE_CSS = (
    ":root{--bg:#f6f6f7;--card:#fff;--fg:#1b1b1f;--muted:#5c5c66;--line:#dcdce0;--field:#b8b8c0;--accent:#1b1b1f;"
    "--accent-fg:#fff;--soft:#f0f0f3;--err:#b3261e;--err-bg:#fdecea}"
    "@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#171a21;--fg:#e8e8ec;--muted:#9a9aa6;"
    "--line:#2a2e38;--field:#3a3f4b;--accent:#e8e8ec;--accent-fg:#111;--soft:#1f232c;--err:#f2b8b5;--err-bg:#3b1715}}"
    "*{box-sizing:border-box}body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--fg);margin:0}"
    "main{max-width:520px;margin:28px auto;padding:0 16px}"
    ".head{display:flex;gap:12px;align-items:center;margin-bottom:16px}"
    ".mark{width:40px;height:40px;border-radius:10px;background:var(--accent);color:var(--accent-fg);display:grid;"
    "place-items:center;font-weight:700;font-size:18px;flex:none}"
    "h1{font-size:20px;margin:0}.sub{margin:2px 0 0;color:var(--muted);font-size:14px}"
    ".tab{position:absolute;opacity:0;pointer-events:none}"
    ".cards{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0}"
    ".card{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center;padding:16px 12px;"
    "border:2px solid var(--line);border-radius:12px;background:var(--card);cursor:pointer;font-weight:400;margin:0}"
    ".card:hover{border-color:var(--field)}.card svg{width:22px;height:22px}"
    ".icon{border-radius:999px;padding:10px;background:var(--soft);color:var(--muted);display:grid}"
    ".card b{font-size:14px}.card small{color:var(--muted);font-size:12px;line-height:1.35}"
    ".group{display:none}.group.only{display:block}"
    ".method{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:12px 0}"
    "h2{font-size:15px;margin:0 0 4px}.desc{color:var(--muted);font-size:13px;margin:0 0 8px;line-height:1.45}"
    "label{display:block;margin:12px 0;font-size:14px;font-weight:500}"
    "input:not(.tab){display:block;width:100%;padding:9px 10px;margin-top:6px;border:1px solid var(--field);"
    "border-radius:8px;font:inherit;background:var(--card);color:var(--fg)}"
    "label small{display:block;color:var(--muted);margin-top:4px;font-weight:400;font-size:12px}"
    "button,.button{display:flex;align-items:center;justify-content:center;width:100%;margin-top:8px;"
    "background:var(--accent);color:var(--accent-fg);border:0;border-radius:8px;padding:10px 16px;font:inherit;"
    "font-weight:600;text-decoration:none;cursor:pointer}"
    ".error{color:var(--err);background:var(--err-bg);border-radius:8px;padding:10px 12px;font-size:14px}"
    "p{font-size:14px;line-height:1.45}code{background:var(--soft);border-radius:4px;padding:1px 4px}"
    ".foot{color:var(--muted);font-size:12px;text-align:center;margin:16px 0 8px}"
)


def _group_css() -> str:
    """Show the selected group and highlight its card: radio buttons and :checked, so the page needs no script."""
    return "".join(
        f"#d-{d}:checked~.g-{d}{{display:block}}"
        f"#d-{d}:checked~.cards .c-{d}{{border-color:var(--accent);background:var(--soft)}}"
        f"#d-{d}:checked~.cards .c-{d} .icon{{background:var(--accent);color:var(--accent-fg)}}"
        f"#d-{d}:focus-visible~.cards .c-{d}{{outline:2px solid var(--accent);outline-offset:2px}}"
        for d in C.DEPLOYMENTS
    )


_CSS = _BASE_CSS + _group_css()
_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true">{}</svg>')
_ICONS = {
    C.DEPLOY_SAAS: _SVG.format('<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>'),
    C.DEPLOY_ON_PREM: _SVG.format('<rect x="2" y="2" width="20" height="8" rx="2"/>'
                                  '<rect x="2" y="14" width="20" height="8" rx="2"/><path d="M6 6h.01M6 18h.01"/>'),
}


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

    @bp.route(C.CONNECT_OAUTH_PATH, methods=["GET"])
    def connect_oauth():
        """The vendor sign-in, started from the panel's Connection dialog with the same one-time nonce."""
        install_id, nonce = request.args.get(FORM_INSTALL_ID, ""), request.args.get(FORM_NONCE, "")
        try:
            redirect_uri = connector.check_nonce(install_id, nonce)
        except ErpError as exc:
            return _page(pack, error=exc.message, status=exc.http_status)
        if connector.oauth is None:
            return _page(pack, error=f"{pack.label} does not use a sign-in page.", status=404)
        return redirect(connector.oauth.auth_url(install_id, redirect_uri), code=302)

    @bp.route(C.CONNECT_API_PATH, methods=["POST"])
    def connect_submit():
        # JSON from the panel's Connection dialog; a form post from the connect page
        as_json = request.is_json
        form = (request.get_json(silent=True) or {}) if as_json else request.form
        install_id, nonce = str(form.get(FORM_INSTALL_ID, "")), str(form.get(FORM_NONCE, ""))
        try:
            next_url = connector.connect_with_credentials(install_id, nonce, str(form.get(FORM_METHOD, "")), form)
        except ErpError as exc:
            if as_json:
                return jsonify(exc.to_dict()), exc.http_status
            return render_page(install_id, nonce, error=exc.message, status=exc.http_status, previous=form)
        if as_json:
            return jsonify({"connected": True, "callback": next_url})
        return redirect(next_url, code=303)

    return bp


def _page(pack: Pack, *, install_id: str = "", nonce: str = "", oauth_url: str | None = None,
          error: str | None = None, status: int = 200, previous: Mapping[str, str] | None = None) -> Response:
    title = f"Connect {pack.label}"
    parts = [f'<header class="head"><div class="mark" aria-hidden="true">{escape(pack.label[:1].upper())}</div>'
             f'<div><h1>{escape(title)}</h1>'
             f'<p class="sub">Choose how AskDiana reaches your {escape(pack.label)} data.</p></div></header>']
    if error:
        parts.append(f'<p class="error" role="alert">{escape(error)}</p>')
    if install_id:
        parts.append(_groups(pack, install_id, nonce, oauth_url, previous or {}))
        parts.append('<p class="foot">Keys and passwords are checked with the system and never shown again.</p>')
    html = (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{escape(title)}</title><style>{_CSS}</style></head>"
        f"<body><main>{''.join(parts)}</main></body></html>"
    )
    return Response(html, status=status, headers=_PAGE_HEADERS, mimetype="text/html")


def _groups(pack: Pack, install_id: str, nonce: str, oauth_url: str | None, previous: Mapping[str, str]) -> str:
    """Cloud / on-prem cards over the login methods. With only one group there is nothing to choose: no cards."""
    groups = deployment_groups(connect_options(pack))
    tried = previous.get(FORM_METHOD)
    chosen = next((g["id"] for g in groups if any(o["method"] == tried for o in g["options"])), groups[0]["id"])
    only = len(groups) == 1
    radios, cards, sections = [], [], []
    for group in groups:
        gid = group["id"]
        checked = " checked" if gid == chosen else ""
        radios.append(f'<input class="tab" type="radio" name="deployment" id="d-{gid}"{checked}>')
        cards.append(f'<label class="card c-{gid}" for="d-{gid}"><span class="icon">{_ICONS[gid]}</span>'
                     f'<b>{escape(group["label"])}</b><small>{escape(group["hint"])}</small></label>')
        blocks = "".join(_method(pack, option, install_id, nonce, oauth_url, previous) for option in group["options"])
        sections.append(f'<section class="group g-{gid}{" only" if only else ""}">{blocks}</section>')
    if only:
        return sections[0]
    return f'{"".join(radios)}<div class="cards">{"".join(cards)}</div>{"".join(sections)}'


def _method(pack: Pack, option: dict, install_id: str, nonce: str, oauth_url: str | None,
            previous: Mapping[str, str]) -> str:
    method = option["method"]
    desc = f'<p class="desc">{escape(option["description"])}</p>' if option["description"] else ""
    if method == C.AUTH_OAUTH2:
        if not oauth_url:
            return ""
        label = escape(option["label"])
        return f'<div class="method"><h2>{label}</h2>{desc}<a class="button" href="{escape(oauth_url)}">{label}</a></div>'
    return f'<div class="method">{_form(pack.auth.credentials[method], install_id, nonce, previous, desc)}</div>'


def _form(spec: CredentialSpec, install_id: str, nonce: str, previous: Mapping[str, str], desc: str = "") -> str:
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
    return (f'<form method="post" action="{_ACTION}"><h2>{escape(spec.label)}</h2>{desc}'
            f'{_hidden(install_id, nonce, spec.method)}{"".join(rows)}<button type="submit">Connect</button></form>')


def _hidden(install_id: str, nonce: str, method: str) -> str:
    return "".join(
        f'<input type="hidden" name="{name}" value="{escape(value)}">'
        for name, value in ((FORM_INSTALL_ID, install_id), (FORM_NONCE, nonce), (FORM_METHOD, method))
    )
