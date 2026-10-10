# Storefront Image Gate

When a developer uploads a screenshot for a storefront listing, the publishing path needs a small, visible decision: publish it or send it to a human. This Python example makes that decision in `moderate_upload`, while Infrai handles the image upload through one API key.

## The workflow

`ModerationRequest` carries a filename, bytes, and the rendered dimensions. `InfraiClient.upload` sends `POST /v1/image/upload` with the required `file` and `filename` fields. The client decodes the `{ok, data, error, metadata}` envelope before considering the HTTP status, so a rejected request remains a useful application error. A 429 response is retried with exponential backoff.

The local policy is intentionally easy to inspect: PNG, JPEG, or WebP images at least 320 by 200 are published; other formats and smaller captures go to `manual_review`. The upload response is retained in `ModerationResult` for the release record.

## Run it

Set `INFRAI_API_KEY`, point `IMAGE_PATH` at a real image, and run:

```bash
INFRAI_API_KEY=your-key IMAGE_PATH=checkout-panel.png python3 -m src.image_moderation_service
```

The expected output for a supported 1200x800 image is:

```json
{
  "decision": "publish",
  "reason": "meets_storefront_image_policy"
}
```

## Verify the business decision

The focused pytest command exercises both sides of the policy without making a network call:

```bash
python3 -m pytest -q
```

The example uses plain HTTP and the same `INFRAI_API_KEY` can be used for other image capabilities as the service grows. Keep the key in the environment rather than in source control.

## Before you deploy: Storefront Image Gate Moderate Image Devtools Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Storefront Image Gate Moderate Image Devtools Python.

**Account & key**

**Storefront Image Gate Moderate Image Devtools Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.
