#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
browser-mcp-python:
- Implements initialize, tools/list, tools/call, prompts/list, resources/list
- Forces UTF-8 stdout/stderr (Windows-safe)
- Tool: medium.publish_from_folder { folder: string }
  * Opens Medium new story and types title + body (very simple MVP)
"""
import json, sys, pathlib, io
from typing import Any, Dict
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ---- Encoding hardening ------------------------------------------------------
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent

def send(o: Dict[str, Any]) -> None:
    # ASCII-safe JSON to avoid codepage issues
    sys.stdout.write(json.dumps(o, ensure_ascii=True) + "\n")
    sys.stdout.flush()

def respond(req_id: int, result: Dict[str, Any]) -> None:
    send({"jsonrpc": "2.0", "id": req_id, "result": result})

def respond_error(req_id: int, code: int, msg: str) -> None:
    send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": msg}})

# ---- Utility -----------------------------------------------------------------
def _split_title_body(markdown: str) -> tuple[str, str]:
    lines = markdown.splitlines()
    if lines and lines[0].lstrip().startswith("# "):
        title = lines[0].lstrip()[2:].strip()
        body = "\n".join(lines[1:]).lstrip()
        return title or "Untitled", body
    # fallback: first non-empty line as title
    for i, ln in enumerate(lines):
        if ln.strip():
            return ln.strip().lstrip("# ").strip() or "Untitled", "\n".join(lines[i + 1 :]).lstrip()
    return "Untitled", markdown

def _load_markdown(folder: pathlib.Path) -> str:
    md = folder / "draft.md"
    if not md.exists():
        raise FileNotFoundError(f"draft.md not found in {folder}")
    return md.read_text(encoding="utf-8")

def publish_from_folder(folder: str) -> Dict[str, Any]:
    fp = pathlib.Path(folder).resolve()
    if not fp.exists():
        return {"ok": False, "error": f"folder not found: {fp}"}

    markdown = _load_markdown(fp)
    title, body = _split_title_body(markdown)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        # Medium new story page
        page.goto("https://medium.com/new-story", wait_until="load", timeout=60000)

        # Click into the editor and type title + body
        try:
            # Title field often grabs focus automatically; ensure focus on body if needed
            page.keyboard.type(title)
            page.keyboard.press("Enter")
            page.keyboard.type("\n" + body)
        except Exception:
            # best effort fallback
            page.click("body")
            page.keyboard.type(title)
            page.keyboard.press("Enter")
            page.keyboard.type("\n" + body)

        page.wait_for_timeout(1500)
        url = page.url
        browser.close()

    return {"ok": True, "url": url}

# ---- MCP main loop -----------------------------------------------------------
def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue

        method = msg.get("method")
        req_id = msg.get("id")

        if method == "initialize":
            respond(req_id, {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "browser-mcp-python", "version": "1.0.1"},
                "capabilities": {"tools": {}}
            })
            send({"jsonrpc": "2.0", "method": "notifications/ready",
                  "params": {"capabilities": {"tools": {}}}})
            continue

        # Prevent Claude timeouts (these are optional but Claude calls them)
        if method == "prompts/list":
            respond(req_id, {"prompts": []})
            continue

        if method == "resources/list":
            respond(req_id, {"resources": []})
            continue

        if method == "tools/list":
            respond(req_id, {
                "tools": [
                    {
                        "name": "medium.publish_from_folder",
                        "description": "Publish a Medium story from a folder containing draft.md",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "folder": {"type": "string"}
                            },
                            "required": ["folder"]
                        }
                    }
                ]
            })
            continue  

        if method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}

            if name == "medium.publish_from_folder":
                folder = args.get("folder")
                if not isinstance(folder, str) or not folder.strip():
                    respond(req_id, {
                        "content": [{"type": "text", "text": json.dumps({"ok": False, "error": "folder (string) required"})}],
                        "isError": True
                    })
                    continue
                try:
                    res = publish_from_folder(folder.strip())
                    respond(req_id, {
                        "content": [{"type": "text", "text": json.dumps(res)}],
                        "isError": not res.get("ok", False)
                    })
                except Exception as e:
                    respond(req_id, {
                        "content": [{"type": "text", "text": json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})}],
                        "isError": True
                    })
                continue

            respond(req_id, {
                "content": [{"type": "text", "text": json.dumps({"ok": False, "error": f"unknown tool: {name}"})}],
                "isError": True
            })
            continue

        if req_id is not None:
            respond_error(req_id, -32601, f"Method not found: {method}")

if __name__ == "__main__":
    main()
