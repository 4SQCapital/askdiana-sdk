import pytest

from tests.test_client_search import _client


def test_data_is_install_scoped_by_default():
    sent = []
    client = _client(sent)
    client.get_data("inst-1", "aml_state", "A-1042")
    client.set_data("inst-1", "aml_state", "A-1042", {"v": 1})
    client.list_data("inst-1", "aml_state")
    client.delete_data("inst-1", "aml_state", "A-1042")
    assert [kwargs["params"] for _, _, kwargs in sent] == [None] * 4


def test_tenant_scope_is_sent_on_every_data_call():
    sent = []
    client = _client(sent)
    client.get_data("inst-1", "aml_state", "A-1042", scope="tenant")
    client.set_data("inst-1", "aml_state", "A-1042", {"v": 1}, scope="tenant")
    client.list_data("inst-1", "aml_state", scope="tenant")
    client.delete_data("inst-1", "aml_state", "A-1042", scope="tenant")
    assert [kwargs["params"] for _, _, kwargs in sent] == [{"scope": "tenant"}] * 4
    assert sent[1][2]["json"] == {"value": {"v": 1}}


def test_an_unknown_scope_is_refused_before_any_request():
    sent = []
    with pytest.raises(ValueError):
        _client(sent).get_data("inst-1", "aml_state", "A-1042", scope="everyone")
    assert sent == []


def test_if_match_is_sent_only_when_given():
    sent = []
    client = _client(sent)
    client.set_data("inst-1", "aml_state", "A-1042", {"v": 2}, scope="tenant", if_match="abc")
    client.set_data("inst-1", "aml_state", "A-1043", {"v": 1}, scope="tenant", if_match="")
    client.set_data("inst-1", "aml_state", "A-1044", {"v": 1})
    assert [kwargs["json"] for _, _, kwargs in sent] == [
        {"value": {"v": 2}, "if_match": "abc"},
        {"value": {"v": 1}, "if_match": ""},
        {"value": {"v": 1}},
    ]
