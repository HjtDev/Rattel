import pytest


class DummyRequest:
    def __init__(self, method="POST", data=None, query_params=None):
        self.method = method
        self.data = data or {}
        self.query_params = query_params or {}


@pytest.fixture
def post_request():
    def _factory(data):
        return DummyRequest(method="POST", data=data)
    return _factory


@pytest.fixture
def get_request():
    def _factory(query_params):
        return DummyRequest(method="GET", query_params=query_params)
    return _factory
