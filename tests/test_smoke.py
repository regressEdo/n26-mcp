from n26_mcp import server, auth, client


def test_imports():
    assert server is not None
    assert auth is not None
    assert client is not None


def test_server_has_mcp():
    assert hasattr(server, "mcp")
