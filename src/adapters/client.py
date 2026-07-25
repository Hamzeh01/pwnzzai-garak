"""Small no-retry client for the verified PwnzzAI HTTP contracts."""

from __future__ import annotations

import hashlib
import ipaddress
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter


_SAFE_UPLOAD_NAME = re.compile(r"^[A-Za-z0-9._-]+[.]png$")


def validate_loopback_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme != "http" or not parsed.hostname:
        raise ValueError("PwnzzAI base URL must use HTTP on a loopback host")
    try:
        is_loopback = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        is_loopback = parsed.hostname.lower() == "localhost"
    if not is_loopback:
        raise ValueError("PwnzzAI base URL must resolve to an explicit loopback host")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("PwnzzAI base URL must not contain credentials or a query")
    return base_url.rstrip("/")


@dataclass(frozen=True)
class HttpExchange:
    method: str
    url: str
    request_headers: dict[str, str]
    request_body: Any
    response_status: int
    response_headers: dict[str, str]
    response_body: Any

    def as_evidence(self) -> dict[str, Any]:
        return {
            "request": {
                "method": self.method,
                "url": self.url,
                "headers": self.request_headers,
                "body": self.request_body,
            },
            "response": {
                "status_code": self.response_status,
                "headers": self.response_headers,
                "body": self.response_body,
            },
        }


@dataclass(frozen=True)
class ApplicationResponse:
    status_code: int
    body: Any
    exchange: HttpExchange


class ApplicationClient:
    """Session-aware transport with explicit timeouts and no automatic retries."""

    def __init__(
        self,
        base_url: str,
        *,
        session: requests.Session | None = None,
        connect_timeout_seconds: float = 5,
    ) -> None:
        self.base_url = validate_loopback_base_url(base_url)
        self.session = session or requests.Session()
        self.session.trust_env = False
        adapter = HTTPAdapter(max_retries=0)
        self.session.mount("http://", adapter)
        self.connect_timeout_seconds = connect_timeout_seconds

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> ApplicationClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def login(
        self, username: str, password: str, *, timeout_seconds: float = 15
    ) -> ApplicationResponse:
        return self._request(
            "POST",
            "/login",
            timeout_seconds=timeout_seconds,
            form={"username": username, "password": password},
            allow_redirects=False,
        )

    def logout(self, *, timeout_seconds: float = 15) -> ApplicationResponse:
        return self._request(
            "GET",
            "/logout",
            timeout_seconds=timeout_seconds,
            allow_redirects=False,
        )

    def get_json(
        self, path: str, *, timeout_seconds: float = 15
    ) -> ApplicationResponse:
        return self._request("GET", path, timeout_seconds=timeout_seconds)

    def post_json(
        self, path: str, body: dict[str, Any], *, timeout_seconds: float
    ) -> ApplicationResponse:
        return self._request(
            "POST",
            path,
            timeout_seconds=timeout_seconds,
            json_body=body,
        )

    def post_empty(
        self, path: str, *, timeout_seconds: float
    ) -> ApplicationResponse:
        return self._request("POST", path, timeout_seconds=timeout_seconds)

    def upload_png(
        self,
        path: str,
        image_path: Path,
        *,
        timeout_seconds: float = 180,
        max_upload_bytes: int = 1024 * 1024,
        remote_filename: str | None = None,
    ) -> ApplicationResponse:
        image = image_path.read_bytes()
        if not image.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("multipart fixture must be a PNG file")
        if len(image) > max_upload_bytes:
            raise ValueError(
                f"multipart fixture exceeds {max_upload_bytes} approved bytes"
            )
        filename = remote_filename or image_path.name
        if not _SAFE_UPLOAD_NAME.fullmatch(filename):
            raise ValueError("remote PNG filename contains unsafe characters")
        summary = {
            "part_name": "file",
            "filename": filename,
            "content_type": "image/png",
            "size_bytes": len(image),
            "sha256": hashlib.sha256(image).hexdigest(),
        }
        return self._request(
            "POST",
            path,
            timeout_seconds=timeout_seconds,
            files={"file": (filename, image, "image/png")},
            evidence_body=summary,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        timeout_seconds: float,
        json_body: dict[str, Any] | None = None,
        form: dict[str, str] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
        evidence_body: Any = None,
        allow_redirects: bool = False,
    ) -> ApplicationResponse:
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("application path must be an absolute path without a host")
        url = urljoin(f"{self.base_url}/", path.lstrip("/"))
        response = self.session.request(
            method,
            url,
            json=json_body,
            data=form,
            files=files,
            timeout=(self.connect_timeout_seconds, timeout_seconds),
            allow_redirects=allow_redirects,
        )
        try:
            response_body: Any = response.json()
        except requests.exceptions.JSONDecodeError:
            response_body = response.text

        request_body = evidence_body
        if request_body is None:
            request_body = json_body if json_body is not None else form

        exchange = HttpExchange(
            method=method,
            url=url,
            request_headers=dict(response.request.headers),
            request_body=request_body,
            response_status=response.status_code,
            response_headers=dict(response.headers),
            response_body=response_body,
        )
        return ApplicationResponse(
            status_code=response.status_code,
            body=response_body,
            exchange=exchange,
        )
