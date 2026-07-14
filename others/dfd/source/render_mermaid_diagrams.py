from __future__ import annotations

import json
import base64
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "source"
EDGE_EXE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
MERMAID_URL = "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def download_mermaid_js(cache_dir: Path) -> Path:
    js_path = cache_dir / "mermaid.min.js"
    if not js_path.exists():
        with urllib.request.urlopen(MERMAID_URL, timeout=30) as response:
            js_path.write_bytes(response.read())
    return js_path


def html_for(source: str, title: str, mermaid_js_path: Path) -> str:
    escaped_source = (
        source.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    js_uri = mermaid_js_path.resolve().as_uri()
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      background: #000;
      color: #f8fafc;
      font-family: Arial, sans-serif;
    }}
    .wrap {{
      display: inline-block;
      padding: 24px;
      background: #000;
    }}
    .title {{
      font-size: 24px;
      font-weight: 700;
      text-align: center;
      margin: 0 0 14px;
      color: #f8fafc;
    }}
    .mermaid {{
      background: #000;
    }}
  </style>
  <script src="{js_uri}"></script>
</head>
<body>
  <div class="wrap">
    <div class="title">{title}</div>
    <pre class="mermaid">
{escaped_source}
    </pre>
  </div>
  <script>
    window.renderStatus = "pending";
    mermaid.initialize({{
      startOnLoad: false,
      theme: "dark",
      securityLevel: "loose",
      flowchart: {{
        useMaxWidth: false,
        htmlLabels: false,
        curve: "basis"
      }}
    }});
    window.addEventListener("load", async () => {{
      try {{
        await mermaid.run({{ querySelector: ".mermaid" }});
        window.renderStatus = "done";
      }} catch (error) {{
        window.renderStatus = "error: " + error.message;
      }}
    }});
  </script>
</body>
</html>
"""


class CDP:
    def __init__(self, ws_url: str):
        self.ws = websocket.create_connection(ws_url, timeout=60, origin="http://localhost")
        self.msg_id = 0

    def call(self, method: str, params: dict | None = None) -> dict:
        self.msg_id += 1
        payload = {"id": self.msg_id, "method": method}
        if params is not None:
            payload["params"] = params
        self.ws.send(json.dumps(payload))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == self.msg_id:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})

    def close(self) -> None:
        self.ws.close()


def wait_for_target(port: int) -> str:
    url = f"http://127.0.0.1:{port}/json/list"
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                targets = json.loads(response.read().decode("utf-8"))
            for target in targets:
                if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                    return target["webSocketDebuggerUrl"]
        except Exception:
            time.sleep(0.2)
    raise TimeoutError("Could not connect to Edge DevTools target.")


def eval_js(cdp: CDP, expression: str, await_promise: bool = False):
    result = cdp.call(
        "Runtime.evaluate",
        {
            "expression": expression,
            "awaitPromise": await_promise,
            "returnByValue": True,
        },
    )
    remote = result.get("result", {})
    return remote.get("value")


def inject_dark_background(svg: str) -> str:
    insert_at = svg.find(">")
    if insert_at == -1:
        return svg
    return svg[: insert_at + 1] + '\n<rect x="-100000" y="-100000" width="200000" height="200000" fill="#000000"/>\n' + svg[insert_at + 1 :]


def render_svg_and_png(source_path: Path, title: str, mermaid_js_path: Path, svg_path: Path, png_path: Path) -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        temp_dir = Path(temp)
        html_path = temp_dir / "diagram.html"
        html_path.write_text(html_for(source_path.read_text(encoding="utf-8"), title, mermaid_js_path), encoding="utf-8")
        port = free_port()
        profile_dir = temp_dir / "edge-profile"
        args = [
            str(EDGE_EXE),
            "--headless=new",
            "--disable-gpu",
            "--disable-extensions",
            "--allow-file-access-from-files",
            "--remote-allow-origins=*",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_dir}",
            html_path.resolve().as_uri(),
        ]
        proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            ws_url = wait_for_target(port)
            cdp = CDP(ws_url)
            try:
                deadline = time.time() + 30
                status = "pending"
                while time.time() < deadline:
                    status = eval_js(cdp, "window.renderStatus")
                    if status == "done" or str(status).startswith("error:"):
                        break
                    time.sleep(0.2)
                if status != "done":
                    raise RuntimeError(f"Mermaid render failed: {status}")
                svg = eval_js(cdp, "document.querySelector('.mermaid svg').outerHTML")
                if not svg:
                    raise RuntimeError("Mermaid rendered no SVG.")
                svg_path.write_text(inject_dark_background(svg), encoding="utf-8")

                rect_json = eval_js(
                    cdp,
                    """
                    JSON.stringify((() => {
                      const r = document.querySelector('.wrap').getBoundingClientRect();
                      return { width: Math.ceil(r.width), height: Math.ceil(r.height) };
                    })())
                    """,
                )
                rect = json.loads(rect_json)
                screenshot = cdp.call(
                    "Page.captureScreenshot",
                    {
                        "format": "png",
                        "captureBeyondViewport": True,
                        "clip": {
                            "x": 0,
                            "y": 0,
                            "width": max(1, rect["width"]),
                            "height": max(1, rect["height"]),
                            "scale": 2,
                        },
                    },
                )
                png_path.write_bytes(base64.b64decode(screenshot["data"]))
            finally:
                cdp.close()
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

def copy_to_legacy_outputs(level: str, png_path: Path) -> None:
    targets = {
        "level-0": ["dfd-level-0-clean-visual.png", "dfd-level-0-detailed-visual.png"],
        "level-1": ["dfd-level-1-clean-visual.png", "dfd-level-1-detailed-visual.png"],
        "level-2": [
            "dfd-level-2-clean-visual.png",
            "dfd-level-2-clean-visual-simplified.png",
            "dfd-level-2-detailed-visual.png",
        ],
    }[level]
    for name in targets:
        (ROOT / level / name).write_bytes(png_path.read_bytes())


def main() -> None:
    if not EDGE_EXE.exists():
        raise SystemExit(f"Microsoft Edge not found at {EDGE_EXE}")

    cache_dir = Path(os.environ.get("TEMP", tempfile.gettempdir())) / "attendance_mermaid_cache"
    cache_dir.mkdir(exist_ok=True)
    mermaid_js_path = download_mermaid_js(cache_dir)

    diagrams = [
        ("level-0", SOURCE_DIR / "dfd-level-0.mmd", "DFD Level 0 - Context Diagram"),
        ("level-1", SOURCE_DIR / "dfd-level-1.mmd", "DFD Level 1 - Main System Processes"),
        ("level-2", SOURCE_DIR / "dfd-level-2.mmd", "DFD Level 2 - Attendance Submission, Review, and Sheet Generation"),
    ]

    for level, source_path, title in diagrams:
        out_dir = ROOT / level
        svg_path = out_dir / f"dfd-{level}-updated.svg"
        png_path = out_dir / f"dfd-{level}-updated.png"
        render_svg_and_png(source_path, title, mermaid_js_path, svg_path, png_path)
        copy_to_legacy_outputs(level, png_path)
        print(f"Wrote {svg_path.relative_to(ROOT)}")
        print(f"Wrote {png_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
