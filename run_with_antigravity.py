#!/usr/bin/env python3
"""
run_with_antigravity.py — All-in-one launcher for autonovel using Antigravity.

Automatically starts the local Antigravity proxy (if not already running)
and executes the specified autonovel script.

Examples:
  uv run python run_with_antigravity.py seed.py
  uv run python run_with_antigravity.py run_pipeline.py --from-scratch
"""

import os
import sys
import time
import subprocess
import threading
import httpx
from antigravity_proxy import ThreadedHTTPServer, AnthropicProxyHandler, HOST, PORT


def is_proxy_running(url=f"http://{HOST}:{PORT}/health") -> bool:
    try:
        r = httpx.get(url, timeout=1.0)
        return r.status_code == 200
    except Exception:
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_with_antigravity.py <script.py> [args...]")
        print("Example: python run_with_antigravity.py seed.py")
        sys.exit(1)

    server = None
    server_thread = None

    if not is_proxy_running():
        print(f"[*] Starting local Antigravity proxy on http://{HOST}:{PORT}...")
        server = ThreadedHTTPServer((HOST, PORT), AnthropicProxyHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        # Wait for proxy readiness
        for _ in range(20):
            if is_proxy_running():
                break
            time.sleep(0.2)
        else:
            print("[-] Failed to start Antigravity proxy.")
            sys.exit(1)
        print("[+] Antigravity proxy is ready!")
    else:
        print(f"[*] Antigravity proxy is already running on http://{HOST}:{PORT}.")

    cmd = [sys.executable] + sys.argv[1:]
    print(f"[*] Executing command: {' '.join(cmd)}")
    print("=" * 60)

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        proc = subprocess.run(cmd, env=env)
        sys.exit(proc.returncode)
    finally:
        if server:
            print("\n[*] Stopping Antigravity proxy...")
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
