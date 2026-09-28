#!/usr/bin/env python3
"""
antigravity_proxy.py — Local Anthropic-to-Antigravity API Adapter.

Translates Anthropic /v1/messages API calls from autonovel scripts
into local Antigravity (`agy`) CLI executions using your authenticated session.
Zero external API keys required!
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("antigravity_proxy")

PORT = int(os.environ.get("ANTIGRAVITY_PROXY_PORT", "8042"))
HOST = os.environ.get("ANTIGRAVITY_PROXY_HOST", "127.0.0.1")

# Locate agy executable
AGY_PATH = shutil.which("agy") or os.path.expanduser(r"~\AppData\Local\agy\bin\agy.exe")

MODEL_MAP: Dict[str, str] = {
    "claude-sonnet-4-6": "claude-sonnet-4-6",
    "claude-sonnet-4-6-20250217": "claude-sonnet-4-6",
    "claude-opus-4-6": "claude-opus-4-6-thinking",
    "claude-opus-4-6-thinking": "claude-opus-4-6-thinking",
    "gemini-3.1-pro": "gemini-3.1-pro-high",
    "gemini-3.1-pro-high": "gemini-3.1-pro-high",
    "gemini-3.8-flash": "gemini-3.8-flash-high",
    "gemini-3.8-flash-high": "gemini-3.8-flash-high",
}

DEFAULT_MODEL = "claude-sonnet-4-6"


def resolve_model(requested_model: str) -> str:
    """Map incoming model name to an available agy model."""
    if not requested_model:
        return DEFAULT_MODEL
    clean_name = requested_model.strip().lower()
    if clean_name in MODEL_MAP:
        return MODEL_MAP[clean_name]
    # Check if requested model contains keywords
    if "opus" in clean_name:
        return "claude-opus-4-6-thinking"
    if "sonnet" in clean_name:
        return "claude-sonnet-4-6"
    if "flash" in clean_name:
        return "gemini-3.8-flash-high"
    if "gemini" in clean_name or "pro" in clean_name:
        return "gemini-3.1-pro-high"
    return clean_name


def format_prompt(payload: Dict[str, Any]) -> str:
    """Combine system instruction and messages into a unified prompt for agy."""
    parts = []

    system = payload.get("system")
    if system:
        if isinstance(system, list):
            # Anthropic sometimes passes system as list of text blocks
            sys_texts = [b.get("text", "") if isinstance(b, dict) else str(b) for b in system]
            system_str = "\n".join(sys_texts).strip()
        else:
            system_str = str(system).strip()

        if system_str:
            parts.append(f"[System Instructions]\n{system_str}\n")

    messages = payload.get("messages", [])
    if isinstance(messages, list):
        if len(messages) == 1 and messages[0].get("role") == "user":
            # Simple single user prompt
            content = messages[0].get("content", "")
            if isinstance(content, list):
                content = "\n".join([b.get("text", "") if isinstance(b, dict) else str(b) for b in content])
            parts.append(str(content))
        else:
            # Multi-turn messages
            dialogue = []
            for msg in messages:
                role = msg.get("role", "user").capitalize()
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = "\n".join([b.get("text", "") if isinstance(b, dict) else str(b) for b in content])
                dialogue.append(f"{role}:\n{content}")
            parts.append("\n\n".join(dialogue))
    elif isinstance(messages, str):
        parts.append(messages)

    return "\n\n".join(parts).strip()


def _execute_agy_process(prompt: str, model: str, timeout: int = 180) -> tuple[str, dict]:
    """Invoke agy stream-json and return (response_text, usage_dict)."""
    if not os.path.exists(AGY_PATH):
        raise FileNotFoundError(f"agy CLI executable not found at '{AGY_PATH}'")

    cmd = [
        AGY_PATH,
        "--model",
        model,
        "--disable-slash-commands",
        "--input-format",
        "stream-json",
        "--output-format",
        "stream-json",
    ]

    input_event = json.dumps({"event": "user", "message": {"content": prompt}}) + "\n"

    logger.info("Executing agy model=%s (prompt length=%d chars)...", model, len(prompt))

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )

    try:
        stdout, stderr = proc.communicate(input=input_event, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise TimeoutError(f"agy timed out after {timeout} seconds")

    if proc.returncode != 0 and not stdout:
        raise RuntimeError(f"agy failed with code {proc.returncode}: {stderr.strip()}")

    response_text = ""
    usage = {"input_tokens": 0, "output_tokens": 0}

    for line in stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        if item.get("event") == "result":
            res = item.get("result", {})
            if res.get("status") == "SUCCESS":
                response_text = res.get("response", "")
                u = res.get("usage", {})
                usage["input_tokens"] = u.get("input_tokens", 0)
                usage["output_tokens"] = u.get("output_tokens", 0)
            elif res.get("status") == "ERROR":
                err_msg = res.get("error", "Unknown agy error")
                raise RuntimeError(f"agy reported error: {err_msg}")

    if not response_text:
        if stderr:
            logger.warning("agy stderr output: %s", stderr.strip())
        if not response_text and stdout:
            response_text = stdout.strip()

    return response_text, usage


def run_agy(prompt: str, target_model: str, timeout: int = 180) -> tuple[str, dict]:
    resolved = resolve_model(target_model)
    candidates = [resolved]
    if "claude" in resolved:
        candidates.append("gemini-3.1-pro-high")

    last_exc = None
    for cand in candidates:
        for attempt in range(2):
            try:
                return _execute_agy_process(prompt, cand, timeout=timeout)
            except Exception as e:
                last_exc = e
                logger.warning("Model %s attempt %d failed: %s", cand, attempt + 1, e)
                time.sleep(2)

    raise last_exc


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class AnthropicProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override to use standard logging
        logger.debug("%s - - [%s] %s", self.address_string(), self.log_date_time_string(), format % args)

    def do_GET(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            status = {
                "status": "ok",
                "service": "antigravity_proxy",
                "agy_path": AGY_PATH,
                "default_model": DEFAULT_MODEL,
            }
            self.wfile.write(json.dumps(status).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path.rstrip("/") != "/v1/messages":
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Endpoint not found"}')
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as e:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Invalid JSON payload: {e}"}).encode("utf-8"))
            return

        requested_model = payload.get("model", "")
        target_model = resolve_model(requested_model)
        prompt = format_prompt(payload)

        try:
            response_text, usage = run_agy(prompt, target_model)
            anthropic_response = {
                "id": f"msg_{uuid.uuid4().hex[:24]}",
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": response_text,
                    }
                ],
                "model": requested_model or target_model,
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                },
            }

            resp_bytes = json.dumps(anthropic_response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            logger.info("Successfully handled request for model=%s -> agy=%s", requested_model, target_model)

        except Exception as e:
            logger.error("Error processing request: %s", e, exc_info=True)
            err_resp = {
                "type": "error",
                "error": {
                    "type": "api_error",
                    "message": str(e),
                },
            }
            err_bytes = json.dumps(err_resp).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err_bytes)))
            self.end_headers()
            self.wfile.write(err_bytes)


def main():
    if not os.path.exists(AGY_PATH):
        logger.error("agy binary not found at %s. Please ensure Antigravity CLI is installed.", AGY_PATH)
        sys.exit(1)

    server = ThreadedHTTPServer((HOST, PORT), AnthropicProxyHandler)
    logger.info("====================================================")
    logger.info("Antigravity Proxy listening on http://%s:%d", HOST, PORT)
    logger.info("Point AUTONOVEL_API_BASE_URL to http://%s:%d", HOST, PORT)
    logger.info("Using agy binary: %s", AGY_PATH)
    logger.info("Ready to intercept Anthropic /v1/messages requests!")
    logger.info("====================================================")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down Antigravity Proxy...")
        server.server_close()


if __name__ == "__main__":
    main()
