import requests

from webexp.cli import check_url


def test_check_url_returns_false_on_connection_error(monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(requests, "get", boom)

    assert check_url("http://127.0.0.1:9/") is False


def test_check_url_returns_false_for_malformed_url():
    assert check_url("notaurl") is False
