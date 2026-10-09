import unittest

import yaml
from flask import Flask

from askdiana.erp import constants as C
from askdiana.erp.connect import connect_blueprint
from askdiana.erp.connection import connect_options, deployment_groups
from askdiana.erp.errors import ErpError
from askdiana.erp.extension import connection_blueprint
from askdiana.erp.pack import _parse_pack
from tests.erp.test_credentials import (API_KEY, AUTH_YAML, INSTALL_ID, REDIRECT_URI, ConnectorTestBase, make_pack,
                                       raw_pack)

# A cloud account (no address to type) next to the self-hosted methods of AUTH_YAML
CLOUD_KEY_YAML = """
token:
  label: Cloud API key
  description: From Settings > API in your cloud account.
  inputs:
    - {name: api_key, label: API key, kind: secret}
  api_base: https://cloud.example/api
  headers: {Authorization: "Bearer {api_key}"}
  test_path: /me
"""


class TestConnectOptions(unittest.TestCase):
    def test_methods_with_an_address_are_on_prem(self):
        options = connect_options(make_pack())
        self.assertEqual([o["method"] for o in options], [C.AUTH_TOKEN, C.AUTH_BASIC, C.AUTH_SESSION])
        self.assertEqual({o["deployment"] for o in options}, {C.DEPLOY_ON_PREM})
        self.assertEqual([i["name"] for i in options[0]["inputs"]], ["base_url", "api_key", "database"])

    def test_no_address_means_saas_and_description_is_kept(self):
        option = connect_options(make_pack(yaml.safe_load(CLOUD_KEY_YAML)))[0]
        self.assertEqual(option["deployment"], C.DEPLOY_SAAS)
        self.assertEqual(option["description"], "From Settings > API in your cloud account.")

    def test_pack_can_set_the_deployment(self):
        auth = yaml.safe_load(CLOUD_KEY_YAML)
        auth["token"]["deployment"] = C.DEPLOY_ON_PREM
        self.assertEqual(connect_options(make_pack(auth))[0]["deployment"], C.DEPLOY_ON_PREM)

    def test_unknown_deployment_is_a_config_error(self):
        auth = yaml.safe_load(CLOUD_KEY_YAML)
        auth["token"]["deployment"] = "hybrid"
        with self.assertRaises(ErpError) as ctx:
            _parse_pack(raw_pack(auth))
        self.assertEqual(ctx.exception.kind, ErpError.CONFIG)

    def test_groups_put_saas_first_and_skip_empty_ones(self):
        auth = {**yaml.safe_load(AUTH_YAML), "token": yaml.safe_load(CLOUD_KEY_YAML)["token"]}
        groups = deployment_groups(connect_options(make_pack(auth)))
        self.assertEqual([g["id"] for g in groups], [C.DEPLOY_SAAS, C.DEPLOY_ON_PREM])
        self.assertEqual([o["method"] for o in groups[1]["options"]], [C.AUTH_BASIC, C.AUTH_SESSION])
        self.assertEqual(len(deployment_groups(connect_options(make_pack()))), 1)


class TestConnectionEndpoint(ConnectorTestBase):
    def setUp(self):
        super().setUp()
        app = Flask("ext")
        app.register_blueprint(connection_blueprint(self.pack, self.connector))
        self.web = app.test_client()

    def status(self) -> dict:
        return self.web.get(C.CONNECTION_STATUS_PATH, query_string={"install_id": INSTALL_ID}).get_json()

    def test_not_connected_lists_the_ways_to_connect(self):
        body = self.status()
        self.assertEqual((body["connected"], body["method"], body["account"]), (False, None, None))
        self.assertEqual(len(body["options"]), 3)
        self.assertEqual(body["groups"][0]["id"], C.DEPLOY_ON_PREM)

    def test_connected_shows_method_and_account_but_no_secrets(self):
        self.connect(C.AUTH_TOKEN, api_key=API_KEY)
        response = self.web.get(C.CONNECTION_STATUS_PATH, query_string={"install_id": INSTALL_ID})
        body = response.get_json()
        self.assertEqual((body["connected"], body["method"], body["method_label"], body["account"]),
                         (True, C.AUTH_TOKEN, "API key", self.erp.base_url))
        self.assertNotIn(API_KEY, response.get_data(as_text=True))

    def test_missing_install_id_is_not_connected(self):
        self.assertFalse(self.web.get(C.CONNECTION_STATUS_PATH).get_json()["connected"])


class TestConnectPageGroups(ConnectorTestBase):
    def page(self, pack) -> str:
        self.pack = pack
        self.connector.pack = pack
        app = Flask("ext")
        app.register_blueprint(connect_blueprint(pack, self.connector))
        return app.test_client().get(C.CONNECT_PAGE_PATH,
                                     query_string={"install_id": INSTALL_ID, "nonce": self.nonce()}).get_data(as_text=True)

    def test_saas_and_on_prem_cards_when_both_exist(self):
        auth = {**yaml.safe_load(AUTH_YAML), "token": yaml.safe_load(CLOUD_KEY_YAML)["token"]}
        html = self.page(make_pack(auth))
        self.assertIn('id="d-saas" checked', html)
        self.assertIn("Cloud (SaaS)", html)
        self.assertIn("Your own server (on-prem)", html)
        self.assertIn("From Settings &gt; API in your cloud account.", html)
        self.assertEqual(html.count("<form"), 3)
        self.assertNotIn("<script", html)

    def test_one_group_has_no_cards(self):
        html = self.page(make_pack())
        self.assertNotIn('class="cards"', html)
        self.assertIn('class="group g-on_prem only"', html)


class TestConnectFromThePanel(ConnectorTestBase):
    """The Connection dialog posts JSON with the nonce AskDiana handed it, and gets JSON back."""

    def setUp(self):
        super().setUp()
        app = Flask("ext")
        app.register_blueprint(connect_blueprint(self.pack, self.connector))
        self.web = app.test_client()

    def post(self, **body):
        return self.web.post(C.CONNECT_API_PATH, json={"install_id": INSTALL_ID, "method": C.AUTH_TOKEN, **body})

    def test_json_success_returns_the_callback(self):
        response = self.post(nonce=self.nonce(), base_url=self.erp.base_url, api_key=API_KEY,
                             askdiana_base_url="https://added.by.the.core.proxy")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["callback"],
                         f"{REDIRECT_URI}?code={C.CONNECTED_CODE}&state={INSTALL_ID}")
        self.assertTrue(self.connector.is_connected(INSTALL_ID))

    def test_json_rejection_is_json_and_the_nonce_still_works(self):
        nonce = self.nonce()
        response = self.post(nonce=nonce, base_url=self.erp.base_url, api_key="wrong-key-value")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["kind"], ErpError.UNAUTHORIZED)
        self.assertNotIn("wrong-key-value", response.get_data(as_text=True))
        retry = self.post(nonce=nonce, base_url=self.erp.base_url, api_key=API_KEY)
        self.assertEqual(retry.status_code, 200)

    def test_json_without_a_valid_nonce_is_refused(self):
        response = self.post(nonce="forged", base_url=self.erp.base_url, api_key=API_KEY)
        self.assertEqual(response.status_code, 401)
        self.assertFalse(self.connector.is_connected(INSTALL_ID))

    def test_oauth_start_needs_a_valid_nonce_and_an_oauth_pack(self):
        forged = self.web.get(C.CONNECT_OAUTH_PATH, query_string={"install_id": INSTALL_ID, "nonce": "forged"})
        self.assertEqual(forged.status_code, 401)
        no_oauth = self.web.get(C.CONNECT_OAUTH_PATH, query_string={"install_id": INSTALL_ID, "nonce": self.nonce()})
        self.assertEqual(no_oauth.status_code, 404)


if __name__ == "__main__":
    unittest.main()
