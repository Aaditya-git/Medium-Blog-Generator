#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
local-runner MCP server:
- Implements initialize, tools/list, tools/call, prompts/list, resources/list
- Forces UTF-8 stdout on Windows to avoid cp1252 UnicodeEncodeError
- Uses ensure_ascii=True when emitting JSON for maximum compatibility
"""
import json, sys, os, pathlib, subprocess, shlex, io

# ---- Encoding hardening (Windows-safe) ---------------------------------------
try:
    # Python 3.7+ supports reconfigure
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    # Fallback for older runtimes
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
ORCHESTRATOR_MODULE = 'src.orchestrator'

def send(o):
    # ASCII-safe JSON to avoid any terminal codepage surprises
    sys.stdout.write(json.dumps(o, ensure_ascii=True) + "\n")
    sys.stdout.flush()

def respond(i, r):
    send({"jsonrpc": "2.0", "id": i, "result": r})

def respond_error(i, code, msg):
    send({"jsonrpc": "2.0", "id": i, "error": {"code": code, "message": msg}})

def safe_tail(txt, n=8000):
    return (txt or "")[-n:]

def run_orchestrator(topic, tone):
    env = os.environ.copy()
    # Ensure orchestrator can import project modules
    env["PYTHONPATH"] = str(REPO_ROOT)
    # Also force UTF-8 at process level
    env["PYTHONIOENCODING"] = env.get("PYTHONIOENCODING", "utf-8")

    cmd = [sys.executable, "-m", ORCHESTRATOR_MODULE, topic]
    if tone:
        cmd += ["--tone", tone]

    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "ran": " ".join(shlex.quote(c) for c in cmd),
        "cwd": str(REPO_ROOT),
        "stdout": safe_tail(proc.stdout),
        "stderr": safe_tail(proc.stderr),
    }

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except Exception:
            # Ignore malformed input
            continue

        method = msg.get("method")
        req_id = msg.get("id")

        # ---- Handshake -------------------------------------------------------
        if method == "initialize":
            respond(req_id, {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "local-runner", "version": "1.0.2"},
                "capabilities": {"tools": {}}
            })
            # Notify ready (helps the client settle)
            send({"jsonrpc": "2.0", "method": "notifications/ready",
                  "params": {"capabilities": {"tools": {}}}})
            continue

        # ---- Prevent Claude Desktop timeouts (these were failing before) -----
        if method == "prompts/list":
            respond(req_id, {"prompts": []})
            continue

        if method == "resources/list":
            respond(req_id, {"resources": []})
            continue

        # ---- Tools catalog ---------------------------------------------------
        if method == "tools/list":
            respond(req_id, {
                "tools": [
                    {
                        "name": "generate_post",
                        "description": "Run orchestrator to create research→outline→draft and save artifacts.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "topic": {"type": "string"},
                                "tone":  {"type": "string"}
                            },
                            "required": ["topic"]
                        }
                    }
                ]
            })
            continue

        # ---- Tool calls ------------------------------------------------------
        if method == "tools/call":
            params = msg.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}

            if name == "generate_post":
                topic = args.get("topic")
                tone  = args.get("tone")

                if not isinstance(topic, str) or not topic.strip():
                    respond(req_id, {
                        "content": [
                            {"type": "text", "text": json.dumps({"ok": False, "error": "topic (string) required"})}
                        ],
                        "isError": True
                    })
                    continue

                result = run_orchestrator(topic.strip(), tone.strip() if isinstance(tone, str) else None)
                respond(req_id, {
                    "content": [{"type": "text", "text": json.dumps(result)}],
                    "isError": not result.get("ok", False)
                })
                continue

            # Unknown tool
            respond(req_id, {
                "content": [{"type": "text", "text": json.dumps({"ok": False, "error": f"unknown tool: {name}"})}],
                "isError": True
            })
            continue

        # ---- Fallback for unhandled methods ---------------------------------
        if req_id is not None:
            respond_error(req_id, -32601, f"Method not found: {method}")

if __name__ == "__main__":
    main()
