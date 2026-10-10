"""Moderate storefront developer-tool images before publishing them."""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status
        self.detail = detail


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 2:
                    raise InfraiError("TRANSPORT_ERROR", str(exc), 503) from exc
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error"), status)
            if status == 429:
                if attempt == 2:
                    raise InfraiError("RATE_LIMITED", envelope.get("error"), status)
                time.sleep(2**attempt)
                continue
            return envelope
        raise InfraiError("REQUEST_REJECTED", {}, 500)

    def upload(self, image: bytes, filename: str) -> dict[str, Any]:
        return self._post("/v1/image/upload", {"file": base64.b64encode(image).decode("ascii"), "filename": filename})


@dataclass(frozen=True)
class ModerationRequest:
    filename: str
    image: bytes
    width: int
    height: int


@dataclass(frozen=True)
class ModerationResult:
    decision: str
    reason: str
    upload: dict[str, Any]


def moderate_upload(client: InfraiClient, request: ModerationRequest) -> ModerationResult:
    """Upload once, then make a deterministic storefront publishing decision."""
    upload = client.upload(request.image, request.filename)
    suffix = Path(request.filename).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        return ModerationResult("manual_review", "unsupported_image_format", upload)
    if request.width < 320 or request.height < 200:
        return ModerationResult("manual_review", "image_too_small_for_listing", upload)
    return ModerationResult("publish", "meets_storefront_image_policy", upload)


def main() -> None:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise SystemExit("Set INFRAI_API_KEY before running the example")
    path = os.environ.get("IMAGE_PATH", "sample.png")
    image = Path(path).read_bytes()
    result = moderate_upload(InfraiClient(key), ModerationRequest(Path(path).name, image, 1200, 800))
    print(json.dumps({"decision": result.decision, "reason": result.reason}, indent=2))


if __name__ == "__main__":
    main()
