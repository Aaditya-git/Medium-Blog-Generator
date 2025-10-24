#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys, io, pathlib
from typing import Any, Dict, Optional
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

HERE = pathlib.Path(__file__).resolve().parent

def send(o): sys.stdout.write(json.dumps(o, ensure_ascii=True) + "\n"); sys.stdout.flush()
def respond(i, r): send({"jsonrpc":"2.0","id":i,"result":r})
def respond_err(i, c, m): send({"jsonrpc":"2.0","id":i,"error":{"code":c,"message":m}})

def _split_title_body(markdown: str):
    lines = markdown.splitlines()
    if lines and lines[0].lstrip().startswith("# "):
        return (lines[0].lstrip()[2:].strip() or "Untitled", "\n".join(lines[1:]).lstrip())
    for i, ln in enumerate(lines):
        if ln.strip():
            return (ln.strip().lstrip("# ").strip() or "Untitled", "\n".join(lines[i+1:]).lstrip())
    return ("Untitled", markdown)

def _load_markdown(folder: pathlib.Path) -> str:
    md = folder / "draft.md"
    if not md.exists(): raise FileNotFoundError(f"draft.md not found in {folder}")
    return md.read_text(encoding="utf-8")

def _open_medium_editor(context, wait_edit_ms=600000):
    page = context.new_page()
    page.goto("https://medium.com/new-story", wait_until="load", timeout=60000)
    try:
        page.wait_for_url("**/new-story**", timeout=15000)
        page.wait_for_selector("div[contenteditable='true']", timeout=15000)
        return page, True
    except PWTimeout:
        pass
    # wait for login to complete
    page.bring_to_front()
    print("[browser-mcp-python] Waiting for Medium editor (sign in if needed)...", file=sys.stderr)
    try:
        page.wait_for_url("**/new-story**", timeout=wait_edit_ms)
        page.wait_for_selector("div[contenteditable='true']", timeout=30000)
        return page, True
    except PWTimeout:
        return page, False

def _launch_chrome(playwright, user_data_dir: str):
    ctx = playwright.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        channel="chrome",
        user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/129.0.0.0 Safari/537.36"),
        args=["--disable-blink-features=AutomationControlled",
              "--no-first-run","--no-default-browser-check"]
    )
    # reduce automation signals
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    return ctx

def _attach_chrome(playwright, cdp_url="http://localhost:9222"):
    browser = playwright.chromium.connect_over_cdp(cdp_url)
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    return browser, ctx

def publish_from_folder(folder: str, pause_for_login: bool = True,
                        attach_to_chrome: bool = False, cdp_url: Optional[str] = None,
                        profile_dir: Optional[str] = None):
    fp = pathlib.Path(folder).resolve()
    if not fp.exists(): return {"ok": False, "error": f"folder not found: {fp}"}

    markdown = _load_markdown(fp)
    title, body = _split_title_body(markdown)

    with sync_playwright() as p:
        if attach_to_chrome:
            browser, context = _attach_chrome(p, cdp_url or "http://localhost:9222")
        else:
            prof = pathlib.Path(profile_dir or (HERE / ".browser_profile")).resolve()
            prof.mkdir(parents=True, exist_ok=True)
            context = _launch_chrome(p, str(prof))
            browser = context.browser

        page, ready = _open_medium_editor(context)
        if not ready:
            return {"ok": False, "error": "Editor not ready (likely not signed in). Sign in in the opened window and re-run."}

        if pause_for_login:
            try:
                page.evaluate("""() => alert('Ready to paste your article. Click OK to paste into the editor.')""")
            except Exception:
                pass

        try:
            page.click("div[contenteditable='true']", timeout=10000)
        except Exception:
            page.click("body", timeout=5000)

        page.keyboard.type(title)
        page.keyboard.press("Enter")
        page.keyboard.type("\n" + body)
        page.wait_for_timeout(1500)
        url = page.url
        return {"ok": True, "url": url}

def main():
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw: continue
        try: msg = json.loads(raw)
        except Exception: continue

        method = msg.get("method"); req_id = msg.get("id")

        if method == "initialize":
            respond(req_id, {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "browser-mcp-python", "version": "2.0"},
                "capabilities": {"tools": {}}
            })
            send({"jsonrpc":"2.0","method":"notifications/ready","params":{"capabilities":{"tools":{}}}})
            continue

        if method == "prompts/list": respond(req_id, {"prompts":[]}); continue
        if method == "resources/list": respond(req_id, {"resources":[]}); continue

        if method == "tools/list":
            respond(req_id, {"tools":[
                {
                    "name":"medium_publish_from_folder",
                    "description":"Open Medium new story and paste draft.md. Can attach to a running Chrome (remote debugging) or launch Chrome with persistent profile.",
                    "inputSchema":{
                        "type":"object",
                        "properties":{
                            "folder":{"type":"string","minLength":3,"pattern":"^[^\\r\\n\\t]{3,}$"},
                            "pause_for_login":{"type":"boolean"},
                            "attach_to_chrome":{"type":"boolean"},
                            "cdp_url":{"type":"string"},
                            "profile_dir":{"type":"string"}
                        },
                        "required":["folder"],
                        "additionalProperties":False
                    }
                }
            ]})
            continue

        if method == "tools/call":
            p = msg.get("params") or {}
            name = p.get("name"); args = p.get("arguments") or {}
            if name == "medium_publish_from_folder":
                try:
                    res = publish_from_folder(
                        folder=(args.get("folder") or "").strip(),
                        pause_for_login=bool(args.get("pause_for_login", True)),
                        attach_to_chrome=bool(args.get("attach_to_chrome", False)),
                        cdp_url=args.get("cdp_url"),
                        profile_dir=args.get("profile_dir")
                    )
                    respond(req_id, {"content":[{"type":"text","text":json.dumps(res)}], "isError": not res.get("ok",False)})
                except Exception as e:
                    respond(req_id, {"content":[{"type":"text","text":json.dumps({"ok":False,"error":f"{type(e).__name__}: {e}"})}], "isError":True})
                continue

            respond(req_id, {"content":[{"type":"text","text":json.dumps({"ok":False,"error":f"unknown tool: {name}"})}],"isError":True})
            continue

        if req_id is not None:
            respond_err(req_id, -32601, f"Method not found: {method}")

if __name__ == "__main__":
    main()
