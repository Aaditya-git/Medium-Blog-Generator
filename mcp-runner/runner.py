#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
local-runner MCP server:
- initialize, tools/list, tools/call, prompts/list, resources/list
- UTF-8 stdout/stderr (Windows-safe)
"""
import json, sys, os, pathlib, subprocess, shlex, io

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
ORCHESTRATOR_MODULE = "src.orchestrator"

def send(o): sys.stdout.write(json.dumps(o, ensure_ascii=True) + "\n"); sys.stdout.flush()
def respond(i, r): send({"jsonrpc": "2.0", "id": i, "result": r})
def respond_error(i, c, m): send({"jsonrpc": "2.0", "id": i, "error": {"code": c, "message": m}})
def safe_tail(t, n=8000): return (t or "")[-n:]

def run_orchestrator(topic, tone):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [sys.executable, "-m", ORCHESTRATOR_MODULE, topic]
    if tone: cmd += ["--tone", tone]
    p = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, env=env)
    return {"ok": p.returncode == 0, "returncode": p.returncode, "ran": " ".join(shlex.quote(c) for c in cmd),
            "cwd": str(REPO_ROOT), "stdout": safe_tail(p.stdout), "stderr": safe_tail(p.stderr)}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try: msg = json.loads(line)
        except Exception: continue

        method = msg.get("method"); req_id = msg.get("id")

        if method == "initialize":
            respond(req_id, {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "local-runner", "version": "1.0.4"},
                "capabilities": {"tools": {}}
            })
            send({"jsonrpc": "2.0", "method": "notifications/ready", "params": {"capabilities": {"tools": {}}}})
            continue

        if method == "prompts/list":
            respond(req_id, {"prompts": []}); continue
        if method == "resources/list":
            respond(req_id, {"resources": []}); continue

        if method == "tools/list":
            respond(req_id, {
                "tools": [{
                    "name": "generate_post",
                    "description": "Run orchestrator to create research→outline→draft and save artifacts.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "minLength": 3,
                                "pattern": "^[^\\r\\n\\t]{3,}$"  # no newlines/tabs, >=3 chars
                            },
                            "tone": {
                                "type": "string",
                                "minLength": 0,
                                "pattern": "^[^\\r\\n\\t]*$"
                            }
                        },
                        "required": ["topic"],
                        "additionalProperties": False
                    }
                }]}
            ); continue

        if method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name"); args = params.get("arguments") or {}
            if name == "generate_post":
                topic = args.get("topic"); tone = args.get("tone")
                if not isinstance(topic, str) or not topic.strip():
                    respond(req_id, {"content":[{"type":"text","text":json.dumps({"ok":False,"error":"topic (non-empty string) required"})}],"isError":True}); continue
                res = run_orchestrator(topic.strip(), tone.strip() if isinstance(tone, str) else None)
                respond(req_id, {"content":[{"type":"text","text":json.dumps(res)}],"isError": (not res.get("ok", False))}); continue

            respond(req_id, {"content":[{"type":"text","text":json.dumps({"ok":False,"error":f"unknown tool: {name}"})}],"isError":True}); continue

        if req_id is not None:
            respond_error(req_id, -32601, f"Method not found: {method}")

if __name__ == "__main__":
    main()
