#!/usr/bin/env python3
"""
test_antigravity_proxy.py — Unit and integration tests for antigravity_proxy.
"""

import threading
import time
import httpx
from antigravity_proxy import (
    resolve_model,
    format_prompt,
    ThreadedHTTPServer,
    AnthropicProxyHandler,
)


def test_resolve_model():
    assert resolve_model("claude-sonnet-4-6") == "claude-sonnet-4-6"
    assert resolve_model("claude-sonnet-4-6-20250217") == "claude-sonnet-4-6"
    assert resolve_model("claude-opus-4-6") == "claude-opus-4-6-thinking"
    assert resolve_model("gemini-3.1-pro") == "gemini-3.1-pro-high"
    assert resolve_model("gemini-3.8-flash") == "gemini-3.8-flash-high"
    print("test_resolve_model passed!")


def test_format_prompt():
    payload1 = {
        "system": "You are a writer.",
        "messages": [{"role": "user", "content": "Write chapter 1."}],
    }
    formatted = format_prompt(payload1)
    assert "[System Instructions]" in formatted
    assert "You are a writer." in formatted
    assert "Write chapter 1." in formatted

    payload2 = {
        "messages": [{"role": "user", "content": "Hello"}],
    }
    assert format_prompt(payload2) == "Hello"
    print("test_format_prompt passed!")


def test_proxy_integration():
    # Start proxy on test port
    test_port = 8899
    server = ThreadedHTTPServer(("127.0.0.1", test_port), AnthropicProxyHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    base_url = f"http://127.0.0.1:{test_port}"

    # 1. Test health check
    health_resp = httpx.get(f"{base_url}/health", timeout=5)
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"
    print("Health check endpoint passed!")

    # 2. Test /v1/messages call via Anthropic-formatted request
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 100,
        "system": "You are a helpful assistant.",
        "messages": [
            {"role": "user", "content": "Respond with exactly the single word: PONG"}
        ],
    }
    headers = {
        "x-api-key": "test_antigravity",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    resp = httpx.post(f"{base_url}/v1/messages", headers=headers, json=payload, timeout=60)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "content" in data
    assert len(data["content"]) > 0
    text = data["content"][0]["text"].strip()
    print(f"Proxy integration response: {text}")
    assert "PONG" in text.upper(), f"Expected PONG in response, got: {text}"

    server.shutdown()
    server.server_close()
    print("Integration test passed successfully!")


if __name__ == "__main__":
    test_resolve_model()
    test_format_prompt()
    test_proxy_integration()
