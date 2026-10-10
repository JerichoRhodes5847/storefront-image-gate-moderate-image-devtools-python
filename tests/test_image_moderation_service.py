import pytest

from src.image_moderation_service import ModerationRequest, moderate_upload


class StubClient:
    def upload(self, image, filename):
        return {"ok": True, "data": {"id": "img_demo"}}


def test_small_listing_image_goes_to_manual_review():
    request = ModerationRequest("checkout-panel.png", b"pixels", 240, 160)
    result = moderate_upload(StubClient(), request)
    assert result.decision == "manual_review"
    assert result.reason == "image_too_small_for_listing"


def test_supported_large_listing_image_is_published():
    request = ModerationRequest("checkout-panel.webp", b"pixels", 1200, 800)
    result = moderate_upload(StubClient(), request)
    assert result.decision == "publish"
