"""本機設計資料庫、風格比較及可還原儲存。"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import shutil
import tempfile
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

import yaml

from vc.project import resolve_project_dir
from vc.style_config import PRESETS, load_style, project_visual_settings, validate_style

ASSET_TYPES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4", ".mov", ".webm", ".json", ".md", ".html", ".txt"}


def _project(root: Path) -> Path:
    root = root.resolve()
    if not (root / "project.yaml").is_file():
        raise FileNotFoundError("Select a video project with project.yaml.")
    for path in (root / "project.yaml", root / "design", root / "design" / "library",
                 root / "design" / "backups", root / "work" / "design"):
        if not path.resolve().is_relative_to(root):
            raise ValueError("Keep workspace paths inside the video project.")
    return root


def _write_json(path: Path, data: dict) -> None:
    _atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2))


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _text(value: object, label: str, required: bool = True) -> str:
    if not isinstance(value, str) or len(value) > 10000 or (required and not value.strip()):
        raise ValueError(f"Set {label} to nonempty text of at most 10000 characters.")
    return value.strip()


def save_brief(root: Path, data: dict) -> Path:
    root = _project(root)
    if not isinstance(data, dict):
        raise ValueError("Set the brief to an object.")  # noqa: TRY004 - 維持一致的輸入驗證介面
    brief = {key: _text(data.get(key), key) for key in ("audience", "purpose", "message")}
    avoid = data.get("avoid", [])
    if not isinstance(avoid, list) or not all(isinstance(item, str) for item in avoid):
        raise ValueError("Set avoid to a list of text values.")
    brief["avoid"] = [_text(item, "avoid") for item in avoid]
    path = root / "design" / "brief.json"
    if path.is_file():
        _backup(root, [path])
    _write_json(path, brief)
    return path


def import_reference(root: Path, source: Path, title: str, origin: str, notes: str, tags: list[str]) -> dict:
    root = _project(root)
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError("Select an existing reference file.")
    if source.suffix.lower() not in ASSET_TYPES:
        raise ValueError("Select an image, video, text, or analysis report.")
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise ValueError("Set tags to a list of text values.")
    record = {"id": uuid4().hex, "title": _text(title, "title"), "source": _text(origin, "source"),
              "notes": _text(notes, "notes", False), "tags": [_text(tag, "tag") for tag in tags],
              "provenance": "user", "asset": "asset" + source.suffix.lower(),
              "imported_at": datetime.now(timezone.utc).isoformat(),
              "sha256": ""}
    with source.open("rb") as stream:
        record["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
    folder = root / "design" / "library" / record["id"]
    folder.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(source, folder / record["asset"])
    _write_json(folder / "record.json", record)
    return record


def _backup(root: Path, paths: list[Path]) -> None:
    folder = root / "design" / "backups" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    for path in paths:
        if path.is_file():
            shutil.copyfile(path, folder / path.name)


def apply_style(root: Path, style: dict, reason: str) -> Path:
    root = _project(root)
    style = validate_style(style)
    reason = _text(reason, "selection reason")
    # 額外排版參數會保存於風格檔，預覽與可支援的渲染器共用。
    typography = style["tokens"]["typography"]
    for key, low, high, default in (("line_height", 1, 2, 1.4), ("letter_spacing_px", -2, 8, 0),
                                     ("content_gap_px", 8, 120, 28)):
        value = typography.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
            raise ValueError(f"Set {key} from {low} to {high}.")
    cfg_path = root / "project.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError("Set project.yaml to an object.")  # noqa: TRY004 - 維持一致的輸入驗證介面
    style_path = root / "design" / "style.json"
    selection = root / "design" / "selection.json"
    _backup(root, [cfg_path, style_path, selection])
    _write_json(style_path, style)
    _write_json(selection, {"reason": reason, "theme_id": style.get("theme_id"),
                            "saved_at": datetime.now(timezone.utc).isoformat()})
    cfg["style"] = "design/style.json"
    _atomic_write(cfg_path, yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False))
    return style_path


def workspace_state(root: Path, scene_id: str, styles: list[str]) -> dict:
    root = _project(root)
    script = json.loads((root / "script.json").read_text(encoding="utf-8-sig"))
    scene = next((item for item in script.get("scenes", []) if item.get("id") == scene_id), None)
    if scene is None:
        raise ValueError("Select an existing scene ID.")
    if not 1 <= len(styles) <= 6:
        raise ValueError("Select from one to six styles.")
    candidates = [{"id": name, "style": load_style(name, root)} for name in styles]
    current, _ = project_visual_settings(root)
    brief_path = root / "design" / "brief.json"
    refs = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((root / "design" / "library").glob("*/record.json"))]
    # 預覽只讀文字，不把參考 HTML 或腳本內的標記當作可執行內容。
    visual = scene.get("visual", scene.get("visuals", {}).get("internal", {}))
    data = visual.get("data", {})
    return {"scene": {"id": scene_id, "title": str(data.get("title", script.get("meta", {}).get("title", scene_id))),
                      "subtitle": str(data.get("subtitle", "")), "narration": str(scene.get("narration", ""))},
            "styles": candidates, "current": current, "references": refs,
            "brief": json.loads(brief_path.read_text(encoding="utf-8")) if brief_path.is_file() else {}}


def _page(state: dict) -> str:
    payload = json.dumps(state, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return Path(__file__).with_name("creative_ui.html").read_text(encoding="utf-8").replace("__STATE__", payload)


def preview(root: Path, scene_id: str, styles: list[str]) -> Path:
    root = _project(root)
    state = workspace_state(root, scene_id, styles)
    path = root / "work" / "design" / "preview.html"
    _atomic_write(path, _page(state))
    return path


def serve(root: Path, scene_id: str, styles: list[str], port: int = 0) -> None:
    root = _project(root)
    state = workspace_state(root, scene_id, styles)
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            return

        def reply(self, status, body, content_type="application/json; charset=utf-8"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))

        def do_GET(self):
            if self.path != "/":
                return self.reply(404, '{}')
            current_state = dict(state, token=token)
            self.reply(200, _page(current_state), "text/html; charset=utf-8")

        def do_POST(self):
            # 同源與隨機 token 同時驗證，避免其他網頁寫入本機專案。
            origin = f"http://127.0.0.1:{self.server.server_port}"
            if self.headers.get("Origin") != origin or self.headers.get("X-VC-Token") != token:
                return self.reply(403, '{"error":"Open the local workspace before you save."}')
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 100000:
                    raise ValueError("Send a request smaller than 100000 bytes.")
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError("Send a JSON object.")  # noqa: TRY004 - 請求錯誤統一回覆 400
                if self.path == "/api/style":
                    apply_style(root, data["style"], data["reason"])
                elif self.path == "/api/brief":
                    save_brief(root, data)
                else:
                    return self.reply(404, '{}')
                self.reply(200, '{"saved":true}')
            except (ValueError, KeyError, TypeError, OSError) as exc:
                self.reply(400, json.dumps({"error": str(exc)}))

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Keep local references and compare scene styles.")
    sub = parser.add_subparsers(dest="command", required=True)
    brief_parser = sub.add_parser("brief")
    brief_parser.add_argument("project")
    for key in ("audience", "purpose", "message"):
        brief_parser.add_argument("--" + key, required=True)
    brief_parser.add_argument("--avoid", action="append", default=[])
    imp = sub.add_parser("import")
    imp.add_argument("project")
    imp.add_argument("source", type=Path)
    imp.add_argument("--title", required=True)
    imp.add_argument("--origin", required=True)
    imp.add_argument("--notes", default="")
    imp.add_argument("--tag", action="append", default=[])
    for command in ("preview", "serve"):
        cmd = sub.add_parser(command)
        cmd.add_argument("project")
        cmd.add_argument("--scene", required=True)
        cmd.add_argument("--styles", nargs="+", default=list(PRESETS[:3]))
        if command == "serve":
            cmd.add_argument("--port", type=int, default=0)
    args = parser.parse_args(argv)
    root = resolve_project_dir(args.project)
    try:
        if args.command == "brief":
            print(save_brief(root, vars(args)))
        elif args.command == "import":
            print(json.dumps(import_reference(root, args.source, args.title, args.origin, args.notes, args.tag), ensure_ascii=False))
        elif args.command == "preview":
            print(preview(root, args.scene, args.styles))
        else:
            serve(root, args.scene, args.styles, args.port)
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
