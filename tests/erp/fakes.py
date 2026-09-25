import os
import threading
from contextlib import contextmanager
from unittest import mock

from werkzeug.serving import make_server


class FakeClient:
    def __init__(self) -> None:
        self.store: dict[tuple[str, str, str], object] = {}

    def set_data(self, install_id, namespace, key, value):
        self.store[(install_id, namespace, key)] = value
        return {"success": True}

    def get_data(self, install_id, namespace, key):
        value = self.store.get((install_id, namespace, key))
        return {"data": {"value": value}} if value is not None else {"data": {}}

    def delete_data(self, install_id, namespace, key):
        self.store.pop((install_id, namespace, key), None)
        return {"success": True}

    def get_config(self, install_id, key):
        return None


class Served:
    def __init__(self, app) -> None:
        self._server = make_server("127.0.0.1", 0, app, threaded=True)
        self.base_url = f"http://127.0.0.1:{self._server.server_port}"
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self._server.shutdown()


@contextmanager
def env(clear: tuple[str, ...] = (), **values: str):
    with mock.patch.dict(os.environ, {}, clear=False):
        for name in clear:
            os.environ.pop(name, None)
        os.environ.update(values)
        yield
