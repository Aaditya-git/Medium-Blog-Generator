#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json, io, pathlib, re, yaml, datetime

# ---- Encoding (Windows-safe)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

def send(o): 
    sys.stdout.write(json.dumps(o, ensure_ascii=True) + "\n"); sys.stdout.flush()
def respond(i, r): 
    send({"jsonrpc": "2.0", "id": i, "result": r})
def respond_err(i, code, msg): 
    send({"jsonrpc":"2.0","id":i,"error":{"code":code,"message":msg}})

# ---- Tiny utils
LINK_RE = re.compile(r'\[([^\]]+)\]\((https?://[^\s)]+)\)')
def today_slug():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def slugify(text: str) -> str:
    import hashlib, re as _re
    t = (text or "").strip().lower()
    base = _re.sub(r"[^a-z0-9]+", "-", t)
    base = _re.sub(r"-{2,}", "-", base).strip("-") or "post"
    return f"{base[:60]}-{hashlib.sha1(t.encode('utf-8')).hexdigest()[:8]}"

def ensure_dir(p: pathlib.Path) -> pathlib.Path:
    p.mkdir(parents=True, exist_ok=True); return p

def write_text(path: pathlib.Path, content: str):
    ensure_dir(path.parent); path.write_text(content, encoding="utf-8")

def extract_refs(markdown: str):
    seen, out = set(), []
    for m in LINK_RE.finditer(markdown or ""):
        title = (m.group(1) or "").strip() or "Untitled"
        url = (m.group(2) or "").strip()
        key = (title.lower(), url)
        if url.startswith("http") and key not in seen:
            seen.add(key); out.append({"title": title, "url": url})
    return out

def output_root():
    cfg = REPO_ROOT / "config" / "app.yaml"
    if cfg.exists():
        try:
            conf = yaml.safe_load(cfg.read_text(encoding="utf-8"))
            root = (REPO_ROOT / conf["paths"]["local_output"]).resolve()
            return ensure_dir(root)
        except Exception:
            pass
    return ensure_dir(REPO_ROOT / "run" / "outputs")

def make_out_folder(topic: str):
    root = output_root()
    folder = root / f"{today_slug()}_{slugify(topic)}"
    # shorten if necessary (Windows MAX_PATH)
    if len(str(folder)) > 240:
        import hashlib
        h8 = hashlib.sha1(str(folder).encode("utf-8")).hexdigest()[:8]
        folder = root / f"{today_slug()}_{h8}"
    return ensure_dir(folder)

def save_post(topic: str, markdown: str, references: list | None):
    out = make_out_folder(topic)

    # Ensure H1 title at top for Medium
    lines = (markdown or "").splitlines()
    if not lines or not lines[0].lstrip().startswith("# "):
        markdown = f"# {topic.strip()}\n\n" + (markdown or "")

    # Write draft.md
    write_text(out / "draft.md", markdown)

    # Write references.txt
    refs = references or extract_refs(markdown)
    if refs:
        acc = today_slug()
        lines = [f"[{i+1}] {r['title']} — {r['url']} (accessed: {acc})" for i, r in enumerate(refs)]
        write_text(out / "references.txt", "\n".join(lines) + "\n")

    # Run log
    write_text(out / "RUNLOG.txt", "Saved via local-runner.save_post (Claude-provided content).\n")
    return {"ok": True, "folder": str(out)}

def main():
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw: 
            continue
        try:
            msg = json.loads(raw)
        except Exception:
            continue

        method = msg.get("method"); req_id = msg.get("id")

        if method == "initialize":
            respond(req_id, {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "local-runner", "version": "2.0"},
                "capabilities": {"tools": {}}
            })
            send({"jsonrpc":"2.0","method":"notifications/ready","params":{"capabilities":{"tools":{}}}})
            continue

        if method == "prompts/list":
            respond(req_id, {"prompts": []}); continue
        if method == "resources/list":
            respond(req_id, {"resources": []}); continue

        if method == "tools/list":
            respond(req_id, {"tools": [
                {
                    "name":"save_post",
                    "description":"Save Claude-written markdown to run/outputs as draft.md (+references.txt).",
                    "inputSchema":{
                        "type":"object",
                        "properties":{
                            "topic":{"type":"string","minLength":3,"pattern":"^[^\\r\\n\\t]{3,}$"},
                            "markdown":{"type":"string","minLength":30},
                            "references":{
                                "type":"array",
                                "items":{
                                    "type":"object",
                                    "properties":{
                                        "title":{"type":"string"},
                                        "url":{"type":"string"},
                                        "accessed":{"type":"string"}
                                    },
                                    "required":["title","url"],
                                    "additionalProperties":True
                                }
                            }
                        },
                        "required":["topic","markdown"],
                        "additionalProperties":False
                    }
                }
            ]})
            continue

        if method == "tools/call":
            p = msg.get("params") or {}
            name = p.get("name"); args = p.get("arguments") or {}

            if name == "save_post":
                topic = (args.get("topic") or "").strip()
                markdown = (args.get("markdown") or "")
                references = args.get("references") or []
                if not topic:
                    respond(req_id, {"content":[{"type":"text","text":json.dumps({"ok":False,"error":"topic required"})}],"isError":True}); continue
                if len(markdown.strip()) < 30:
                    respond(req_id, {"content":[{"type":"text","text":json.dumps({"ok":False,"error":"markdown too short"})}],"isError":True}); continue
                try:
                    res = save_post(topic, markdown, references)
                    respond(req_id, {"content":[{"type":"text","text":json.dumps(res)}],"isError": not res.get("ok",False)})
                except Exception as e:
                    respond(req_id, {"content":[{"type":"text","text":json.dumps({"ok":False,"error":f"{type(e).__name__}: {e}"})}],"isError":True})
                continue

            respond(req_id, {"content":[{"type":"text","text":json.dumps({"ok":False,"error":f"unknown tool: {name}"})}],"isError":True})
            continue

        if req_id is not None:
            respond_err(req_id, -32601, f"Method not found: {method}")

if __name__ == "__main__":
    main()
