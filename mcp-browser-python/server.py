#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
browser-mcp-python:
- initialize, tools/list, tools/call, prompts/list, resources/list
- UTF-8 stdout/stderr (Windows-safe)
- Tools:
    medium_publish_from_folder { folder: string, pause_for_login?: bool, profile_dir?: string }
    web_search_topn (optional; leave as-is if you already added it)
"""
import json, sys, pathlib, io, os
import platform 
from typing import Any, Dict, List, Optional
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
    sys.stdout.write(json.dumps(o, ensure_ascii=True) + "\n")
    sys.stdout.flush()

def respond(req_id: int, result: Dict[str, Any]) -> None:
    send({"jsonrpc": "2.0", "id": req_id, "result": result})

def respond_error(req_id: int, code: int, msg: str) -> None:
    send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": msg}})

def _launch_humanlike_chrome(playwright, user_data_dir: str):
    """
    Launch a persistent Chrome context with settings that reduce automation signals.
    """
    # You can hard-pin a Chrome executable if Playwright can't find it:
    # exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process,OptimizationHints",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=Translate",
        "--disable-extensions",  # remove if you actually rely on extensions
        "--password-store=basic",
    ]

    # A recent stable UA (keep this updated every few months)
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36"
    )

    ctx = playwright.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        channel="chrome",        # use real Chrome
        headless=False,
        args=args,
        viewport={"width": 1366, "height": 900},
        user_agent=ua,
        locale="en-US",
    )

    # Remove navigator.webdriver & a few obvious hints
    ctx.add_init_script("""
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
window.chrome = { runtime: {} };
    """)
    return ctx

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

def _default_profile_dir() -> pathlib.Path:
    # Keep this inside your repo by default so it's obvious/persisted
    return (HERE / ".browser_profile").resolve()

def _open_medium_editor(context, long_wait_ms: int = 600_000):
    """Open Medium editor and wait until the editor UI is ready (not login)."""
    page = context.new_page()
    page.goto("https://medium.com/new-story", wait_until="load", timeout=60_000)

    # If login is required, Medium will redirect to /m/signin or show auth UI.
    # We DO NOT type anything until the real editor is visible.
    # Conditions to consider 'logged in & editor ready':
    #  - URL ends with /new-story AND the contenteditable editor is present.
    #  - Or a known editor selector exists.
    editor_ready = False
    try:
        page.wait_for_url("**/new-story**", timeout=10_000)
        # give the editor time to mount
        page.wait_for_selector("div[contenteditable='true']", timeout=10_000)
        editor_ready = True
    except PWTimeout:
        pass

    if not editor_ready:
        # Likely on login: wait (up to ~10 minutes) for user to complete login
        # and for editor to be ready. We just poll for editor selector.
        # This lets you manually sign in without the bot typing into fields.
        page.bring_to_front()
        page.evaluate("() => window.focus && window.focus()")
        # Informative console message (goes to MCP log)
        print("[browser-mcp-python] Waiting for you to sign in to Medium... (up to 10 minutes)", file=sys.stderr)
        try:
            page.wait_for_url("**/new-story**", timeout=long_wait_ms)
            page.wait_for_selector("div[contenteditable='true']", timeout=30_000)
            editor_ready = True
        except PWTimeout:
            pass

    return page, editor_ready

def publish_from_folder(folder: str, pause_for_login: bool = True, profile_dir: Optional[str] = None) -> Dict[str, Any]:
    fp = pathlib.Path(folder).resolve()
    if not fp.exists():
        return {"ok": False, "error": f"folder not found: {fp}"}

    markdown = _load_markdown(fp)
    title, body = _split_title_body(markdown)

    # Persistent profile so you stay signed in after first login
    profile_root = pathlib.Path(profile_dir).resolve() if profile_dir else _default_profile_dir()
    profile_root.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        context = _launch_humanlike_chrome(p, str(profile_root))


        page, editor_ready = _open_medium_editor(context)

        if not editor_ready:
            # You didn't finish login within the wait window.
            # Leave the browser open so you can complete it and re-run the tool.
            return {
                "ok": False,
                "error": "Medium editor not ready (likely not signed in yet). Complete login in the opened window, then re-run.",
                "hint": "You can keep this window open; the profile is persistent so future runs will be signed in."
            }

        # Optional: let user confirm before we paste
        if pause_for_login:
            # Show a small non-blocking prompt using a harmless alert (works in page context)
            try:
                page.evaluate("""() => alert('Ready to paste your article. Click OK when you want me to paste the content into the editor.');""")
            except Exception:
                pass  # ignore if alerts are blocked

        # Focus editor and paste content only now
        try:
            # Focus any rich text area
            page.click("div[contenteditable='true']", timeout=10_000)
        except Exception:
            # Fallback to body
            page.click("body", timeout=5_000)

        # Type the title then the body. We avoid typing into login forms by waiting above.
        page.keyboard.type(title)
        page.keyboard.press("Enter")
        page.keyboard.type("\n" + body)

        # give Medium time to autosave
        page.wait_for_timeout(1500)
        url = page.url

        # Keep the window open so you can review before publishing
        # (close it manually or change to context.close() if you want auto-close)
        return {"ok": True, "url": url, "profile": str(profile_root)}

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
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "browser-mcp-python", "version": "1.1.0"},
                "capabilities": {"tools": {}}
            })
            send({"jsonrpc": "2.0", "method": "notifications/ready",
                  "params": {"capabilities": {"tools": {}}}})
            continue

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
                        "name": "medium_publish_from_folder",
                        "description": "Open Medium new story and paste draft.md after login is complete. Uses a persistent browser profile.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "folder": { "type": "string", "minLength": 3, "pattern": "^[^\\r\\n\\t]{3,}$" },
                                "pause_for_login": { "type": "boolean" },
                                "profile_dir": { "type": "string" }
                            },
                            "required": ["folder"],
                            "additionalProperties": False
                        }
                    }
                ]
            })
            continue

        if method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}

            if name == "medium_publish_from_folder":
                folder = args.get("folder")
                pause_for_login = bool(args.get("pause_for_login", True))
                profile_dir = args.get("profile_dir")
                if not isinstance(folder, str) or not folder.strip():
                    respond(req_id, {
                        "content": [{"type": "text", "text": json.dumps({"ok": False, "error": "folder (non-empty string) required"})}],
                        "isError": True
                    })
                    continue
                try:
                    res = publish_from_folder(folder.strip(), pause_for_login=pause_for_login, profile_dir=profile_dir)
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
