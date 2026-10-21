from askdiana import AskDianaClient


class _Response:
    status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return {"success": True, "results": []}


def _client(sent):
    client = AskDianaClient(api_key="askd_test", base_url="https://ask.example/")

    def request(method, url, **kwargs):
        sent.append((method, url, kwargs))
        return _Response()

    client._session.request = request
    return client


def test_search_documents_posts_the_query():
    sent = []
    assert _client(sent).search_documents("inst-1", "can I close this", project_id="p1", limit=5) == {
        "success": True,
        "results": [],
    }
    method, url, kwargs = sent[0]
    assert (method, url) == ("POST", "https://ask.example/api/ext/documents/search")
    assert kwargs["headers"] == {"X-Install-Id": "inst-1"}
    assert kwargs["json"] == {"query": "can I close this", "limit": 5, "project_id": "p1"}


def test_search_documents_passes_document_ids_even_when_empty():
    sent = []
    _client(sent).search_documents("inst-1", "loan", document_ids=[])
    assert sent[0][2]["json"] == {"query": "loan", "limit": 8, "document_ids": []}
