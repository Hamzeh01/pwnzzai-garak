from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar
from urllib.parse import parse_qs

import openai
import pytest

from src.adapters import ApplicationClient, PwnzzAIOpenAICompatible


class ContractHandler(BaseHTTPRequestHandler):
    scanner_requests: ClassVar[int] = 0
    login_requests: ClassVar[int] = 0
    logout_cookie: ClassVar[str | None] = None
    multipart_ok: ClassVar[bool] = False
    scanner_status: ClassVar[int] = 200
    scanner_request_body: ClassVar[dict[str, object] | None] = None

    def do_GET(self) -> None:
        if self.path != "/logout":
            self.send_error(404)
            return
        type(self).logout_cookie = self.headers.get("Cookie")
        self.send_response(302)
        self.send_header("Location", "/")
        self.send_header(
            "Set-Cookie",
            "session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/",
        )
        self.end_headers()

    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if self.path == "/login":
            type(self).login_requests += 1
            form = parse_qs(body.decode("utf-8"))
            if form != {"username": ["alice"], "password": ["public-fixture"]}:
                self.send_error(400)
                return
            self.send_response(302)
            self.send_header("Location", "/")
            self.send_header(
                "Set-Cookie",
                "session=synthetic-session-value; HttpOnly; Path=/",
            )
            self.end_headers()
            return

        if self.path == "/upload-qr":
            content_type = self.headers.get("Content-Type", "")
            type(self).multipart_ok = (
                content_type.startswith("multipart/form-data; boundary=")
                and b'name="file"' in body
                and b"image/png" in body
                and b"\x89PNG\r\n\x1a\n" in body
            )
            self._json_response(
                200,
                {
                    "response": "Synthetic benign QR response.",
                    "qr_text": "What pizza choices are available today?",
                },
            )
            return

        if self.path == "/v1/lab/chat/completions":
            type(self).scanner_requests += 1
            if type(self).scanner_status == 500:
                self._json_response(
                    500,
                    {
                        "error": {
                            "message": "Synthetic unavailable response.",
                            "type": "server_error",
                        }
                    },
                )
                return
            request = json.loads(body)
            type(self).scanner_request_body = request
            assert request["pwnzz_escalation_stage"] in {0, 6}
            assert request["messages"][0]["content"] == "What pizzas do you offer?"
            self._json_response(
                200,
                {
                    "id": "chatcmpl-synthetic",
                    "object": "chat.completion",
                    "created": 1784995200,
                    "model": "lab-direct-prompt-escalation",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "Synthetic benign pizza menu response.",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "pwnzz_escalation_meta": {
                        "stage": 0,
                        "title": "Synthetic stage",
                    },
                },
            )
            return

        self.send_error(404)

    def log_message(self, *_: object) -> None:
        return

    def _json_response(self, status: int, value: dict[str, object]) -> None:
        payload = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _start_server(
    *, scanner_status: int = 200
) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    ContractHandler.scanner_requests = 0
    ContractHandler.login_requests = 0
    ContractHandler.logout_cookie = None
    ContractHandler.multipart_ok = False
    ContractHandler.scanner_status = scanner_status
    ContractHandler.scanner_request_body = None
    server = ThreadingHTTPServer(("127.0.0.1", 0), ContractHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, thread, f"http://{host}:{port}"


def test_session_and_multipart_contracts(tmp_path: Path) -> None:
    server, thread, base_url = _start_server()
    try:
        image_path = tmp_path / "benign.png"
        image_path.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic")
        with ApplicationClient(base_url) as client:
            login = client.login("alice", "public-fixture")
            upload = client.upload_png("/upload-qr", image_path)
            logout = client.logout()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert login.status_code == 302
    assert upload.status_code == 200
    assert logout.status_code == 302
    assert ContractHandler.login_requests == 1
    assert ContractHandler.logout_cookie == "session=synthetic-session-value"
    assert ContractHandler.multipart_ok is True
    assert upload.exchange.request_body["part_name"] == "file"
    assert "synthetic" not in json.dumps(upload.exchange.request_body)


def test_multipart_contract_enforces_size_and_remote_filename(tmp_path: Path) -> None:
    image_path = tmp_path / "benign.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic")
    with ApplicationClient("http://127.0.0.1:9") as client:
        with pytest.raises(ValueError, match="approved bytes"):
            client.upload_png(
                "/upload-qr",
                image_path,
                max_upload_bytes=8,
            )
        with pytest.raises(ValueError, match="unsafe"):
            client.upload_png(
                "/upload-qr",
                image_path,
                remote_filename="../escape.png",
            )


def test_garak_scanner_path_sends_exactly_one_request_and_retains_metadata() -> None:
    server, thread, base_url = _start_server()
    try:
        with PwnzzAIOpenAICompatible(base_url, stage=0) as generator:
            result = generator.generate_once("What pizzas do you offer?")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert ContractHandler.scanner_requests == 1
    assert result.output == "Synthetic benign pizza menu response."
    assert result.exchange.status_code == 200
    assert result.exchange.response_body["pwnzz_escalation_meta"]["stage"] == 0
    assert result.exchange.request_body["pwnzz_escalation_stage"] == 0


def test_garak_scanner_path_preserves_multiturn_messages() -> None:
    server, thread, base_url = _start_server()
    messages = [
        {"role": "user", "content": "What pizzas do you offer?"},
        {"role": "assistant", "content": "Synthetic menu."},
        {"role": "user", "content": "What pizzas do you offer?"},
    ]
    try:
        with PwnzzAIOpenAICompatible(base_url, stage=6) as generator:
            generator.generate_messages_once(messages)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert ContractHandler.scanner_request_body is not None
    assert ContractHandler.scanner_request_body["messages"] == messages
    assert ContractHandler.scanner_request_body["pwnzz_escalation_stage"] == 6


def test_garak_scanner_path_does_not_retry_server_error() -> None:
    server, thread, base_url = _start_server(scanner_status=500)
    try:
        with PwnzzAIOpenAICompatible(base_url, stage=0) as generator:
            with pytest.raises(openai.InternalServerError):
                generator.generate_once("What pizzas do you offer?")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert ContractHandler.scanner_requests == 1
