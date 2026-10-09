from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests

from . import constants as C
from .connector import ErpConnector
from .errors import ErpError
from .pack import Pack
from .session import Session


class DirectTransport:
    def __init__(self, connector: ErpConnector, pack: Pack):
        self._connector = connector
        self._pack = pack

    def get(self, install_id: str, path: str, params: Mapping[str, Any]) -> requests.Response:
        return self.request(install_id, C.METHOD_GET, path, params)

    def request(self, install_id: str, method: str, path: str, params: Mapping[str, Any],
                body: Any = None) -> requests.Response:
        response = self._send(self._session(install_id), method, path, params, body)
        if response.status_code == C.HTTP_UNAUTHORIZED:
            response = self._send(self._session(install_id, force_refresh=True), method, path, params, body)
        self._raise_for_status(response)
        return response

    def _session(self, install_id: str, *, force_refresh: bool = False) -> Session:
        session = self._connector.session(install_id, force_refresh=force_refresh)
        if session is None:
            raise ErpError(ErpError.NOT_CONNECTED,
                           f"{self._pack.label} is not connected. Connect your account from the Marketplace card.")
        return session

    def _send(self, session: Session, method: str, path: str, params: Mapping[str, Any],
              body: Any = None) -> requests.Response:
        try:
            if method == C.METHOD_GET:
                return session.get(path, params)
            return session.send(method, path, params, body)
        except requests.RequestException as exc:
            raise ErpError(ErpError.VENDOR, f"{self._pack.label} could not be reached: {exc}") from exc

    def _raise_for_status(self, response: requests.Response) -> None:
        status = response.status_code
        if status < C.HTTP_CLIENT_ERROR_MIN:
            return
        label = self._pack.label
        if status == C.HTTP_UNAUTHORIZED:
            raise ErpError(ErpError.UNAUTHORIZED, f"{label} rejected the saved login. Reconnect your account.", vendor_status=status)
        if status == C.HTTP_TOO_MANY_REQUESTS:
            raise ErpError(ErpError.RATE_LIMITED, f"{label} API limit reached. Try again later.", vendor_status=status)
        raise ErpError(ErpError.VENDOR, f"{label} returned HTTP {status}: {response.text[:C.ERROR_BODY_PREVIEW_CHARS]}",
                       vendor_status=status)
