"""The pack's login methods as connect options, grouped SaaS / on-prem.

Used by the connect page and by GET /api/connection (the panel's Connection dialog). Never includes
secrets or stored values: only labels, descriptions and the inputs each method asks for.
"""
from __future__ import annotations

from typing import Any

from . import constants as C
from .pack import CredentialSpec, Pack

DEPLOYMENT_LABELS = {C.DEPLOY_SAAS: "Cloud (SaaS)", C.DEPLOY_ON_PREM: "Your own server (on-prem)"}
DEPLOYMENT_HINTS = {
    C.DEPLOY_SAAS: "Sign in to the vendor's cloud service.",
    C.DEPLOY_ON_PREM: "Connect to a system you host, or to your own app or keys.",
}


def credential_deployment(spec: CredentialSpec) -> str:
    """A method that asks for an address is a self-hosted system; one that doesn't is a cloud account."""
    if spec.deployment:
        return spec.deployment
    return C.DEPLOY_ON_PREM if any(item.kind == C.INPUT_URL for item in spec.inputs) else C.DEPLOY_SAAS


def connect_options(pack: Pack) -> list[dict[str, Any]]:
    """One entry per login method, in pack order."""
    auth, options = pack.auth, []
    for method in auth.methods:
        if method == C.AUTH_OAUTH2:
            spec = auth.oauth2
            options.append(_option(method, spec.label, spec.description, spec.deployment or C.DEPLOY_SAAS, []))
        else:
            spec = auth.credentials[method]
            inputs = [{"name": i.name, "label": i.label, "kind": i.kind, "required": i.required, "help": i.help}
                      for i in spec.inputs]
            options.append(_option(method, spec.label, spec.description, credential_deployment(spec), inputs))
    return options


def deployment_groups(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Options grouped by deployment, SaaS first; groups without options are left out."""
    return [{"id": d, "label": DEPLOYMENT_LABELS[d], "hint": DEPLOYMENT_HINTS[d],
             "options": [o for o in options if o["deployment"] == d]}
            for d in C.DEPLOYMENTS if any(o["deployment"] == d for o in options)]


def _option(method: str, label: str, description: str | None, deployment: str, inputs: list) -> dict[str, Any]:
    return {"method": method, "label": label, "description": description, "deployment": deployment,
            "inputs": inputs}
