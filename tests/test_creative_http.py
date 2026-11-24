"""驗證本機工作區的寫入邊界與可觀察回應。"""
import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from vc import creative
from vc.style_config import load_style


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    root = tmp_path / "project"
    root.mkdir()
    (root / "project.yaml").write_text("name: example\n", encoding="utf-8")
    (root / "script.json").write_text(json.dumps({"scenes": [{"id": "s01", "narration": "Explanation"}]}))
    ready = threading.Event()
    holder = {}

    class Server(ThreadingHTTPServer):
        def serve_forever(self, **kwargs):
            holder["server"] = self
            ready.set()
            super().serve_forever(**kwargs)

    monkeypatch.setattr(creative, "ThreadingHTTPServer", Server)
    monkeypatch.setattr(creative.secrets, "token_urlsafe", lambda _: "test-token")
    thread = threading.Thread(target=creative.serve, args=(root, "s01", ["executive_navy"]), daemon=True)
    thread.start()
    assert ready.wait(5)
    server = holder["server"]
    yield root, server.server_port
    server.shutdown()
    thread.join(5)
    assert not thread.is_alive()


def request(workspace, method, path, data=None, token="test-token", origin=True):
    _, port = workspace
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {"X-VC-Token": token, "Content-Type": "application/json"}
    if origin:
        headers["Origin"] = f"http://127.0.0.1:{port}"
    conn.request(method, path, body=json.dumps(data) if data is not None else None, headers=headers)
    response = conn.getresponse()
    body = response.read().decode("utf-8")
    result = response.status, body
    conn.close()
    return result


def test_read_only_preview_and_explicit_save(workspace):
    root, _ = workspace
    before = (root / "project.yaml").read_bytes()
    status, html = request(workspace, "GET", "/")
    assert status == 200
    assert "test-token" in html
    assert (root / "project.yaml").read_bytes() == before
    status, _ = request(workspace, "POST", "/api/style", {"style": load_style(), "reason": "Readable hierarchy"})
    assert status == 200
    assert (root / "design/style.json").is_file()
    assert list((root / "design/backups").glob("*/project.yaml"))


@pytest.mark.parametrize("token,origin", [("wrong", True), ("test-token", False)])
def test_reject_cross_site_writes(workspace, token, origin):
    status, _ = request(workspace, "POST", "/api/style", {"style": load_style(), "reason": "example"}, token, origin)
    assert status == 403
    assert not (workspace[0] / "design/style.json").exists()


@pytest.mark.parametrize("data", [[], {"style": {}}, {"style": load_style(), "reason": ""}])
def test_reject_invalid_save_without_changing_project(workspace, data):
    root, _ = workspace
    before = (root / "project.yaml").read_bytes()
    status, _ = request(workspace, "POST", "/api/style", data)
    assert status == 400
    assert (root / "project.yaml").read_bytes() == before


def test_does_not_serve_arbitrary_project_files(workspace):
    assert request(workspace, "GET", "/../project.yaml")[0] == 404


@pytest.mark.parametrize("value", [[], None, "text"])
def test_reject_non_object_brief(tmp_path, value):
    (tmp_path / "project.yaml").write_text("name: example\n")
    with pytest.raises(ValueError, match="object"):
        creative.save_brief(tmp_path, value)
