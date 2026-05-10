#!/usr/bin/env python3
"""
Tests for webhook payload building and sending.
Covers payload structure, field validation, and mock HTTP sending.
"""

import sys
import json
import uuid
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.send_to_webhook import (
    build_webhook_payload,
    send_to_webhook,
    encode_zip_base64,
)
from utils.config_loader import load_config


def make_sample_manifest(image_count: int = 50) -> dict:
    return {
        "pack_id": str(uuid.uuid4()),
        "run_id": str(uuid.uuid4()),
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pack": {
            "theme": "cosmic_nebula",
            "style": "watercolor",
            "image_count": image_count,
            "theme_display": "Cosmic Nebula",
            "style_display": "Watercolor",
        },
        "files": {
            "images": [{"filename": f"img_{i}.png"} for i in range(image_count)],
            "zip": {
                "filename": "cosmic_nebula_20240101.zip",
                "path": "output/zips/cosmic_nebula_20240101.zip",
                "size_bytes": 1024 * 1024 * 15,
                "size_mb": 15.0,
                "sha256": "abc123",
            },
            "gdrive_path": "AI Art Packs/2024-01/cosmic_nebula",
        },
        "seo": {
            "etsy": {
                "title": "Cosmic Nebula Watercolor Digital Art Pack | 50 High Res Images | Commercial Use",
                "description": "Beautiful cosmic nebula art pack...",
                "tags": [
                    "digital art", "instant download", "commercial use",
                    "cosmic art", "space art", "nebula art", "watercolor",
                    "galaxy art", "digital download", "printable art",
                    "wall art", "art bundle", "high resolution",
                ],
                "price_usd": 14.99,
                "category": "Art & Collectibles > Prints > Digital Prints",
                "shipping_profile": "digital_download",
            },
            "creative_market": {
                "title": "50 Cosmic Nebula Watercolor Background Images Bundle",
                "description": "Premium cosmic nebula backgrounds...",
                "keywords": [
                    "cosmic backgrounds", "nebula images", "space art",
                    "digital backgrounds", "watercolor space", "galaxy",
                    "commercial license", "high resolution", "PNG files",
                    "instant download", "design assets", "creative bundle",
                    "background bundle", "cosmic art", "universe",
                ],
            },
            "adobe_stock": [
                {
                    "title": "Cosmic nebula watercolor - ethereal digital background",
                    "keywords": [
                        "cosmic", "nebula", "space", "watercolor", "digital art",
                        "background", "galaxy", "stars", "universe", "astronomy",
                        "abstract", "blue", "purple", "ethereal", "mystical",
                    ],
                    "category": "Backgrounds/Textures",
                },
            ],
        },
        "marketplace_ready": {
            "etsy": True,
            "creative_market": True,
            "adobe_stock": True,
        },
        "license": {
            "type": "Commercial Use",
            "personal_use": True,
            "commercial_use": True,
            "resale_of_files": False,
            "attribution_required": False,
            "ai_generated": True,
            "ai_disclosure": "Images generated using AI",
        },
        "config_snapshot": {
            "provider": "openai",
            "model": "dall-e-3",
            "image_size": "1024x1024",
            "quality": "hd",
        },
    }


class TestPayloadBuilding(unittest.TestCase):
    def setUp(self):
        self.manifest = make_sample_manifest()

    def test_payload_is_dict(self):
        payload = build_webhook_payload(self.manifest)
        self.assertIsInstance(payload, dict)

    def test_payload_has_pack_id(self):
        payload = build_webhook_payload(self.manifest)
        self.assertIn("pack_id", payload)
        self.assertEqual(payload["pack_id"], self.manifest["pack_id"])

    def test_payload_has_theme(self):
        payload = build_webhook_payload(self.manifest)
        self.assertEqual(payload["theme"], "cosmic_nebula")

    def test_payload_has_style(self):
        payload = build_webhook_payload(self.manifest)
        self.assertEqual(payload["style"], "watercolor")

    def test_payload_has_image_count(self):
        payload = build_webhook_payload(self.manifest)
        self.assertEqual(payload["image_count"], 50)

    def test_payload_has_etsy_fields(self):
        payload = build_webhook_payload(self.manifest)
        for field in ("etsy_title", "etsy_description", "etsy_tags", "etsy_price_usd", "etsy_category"):
            self.assertIn(field, payload, f"Missing Etsy field: {field}")

    def test_payload_etsy_tags_is_list(self):
        payload = build_webhook_payload(self.manifest)
        self.assertIsInstance(payload["etsy_tags"], list)
        self.assertEqual(len(payload["etsy_tags"]), 13)

    def test_payload_etsy_tags_string_is_comma_separated(self):
        payload = build_webhook_payload(self.manifest)
        tags_str = payload["etsy_tags_string"]
        self.assertIn(",", tags_str)
        self.assertEqual(len(tags_str.split(", ")), 13)

    def test_payload_has_creative_market_fields(self):
        payload = build_webhook_payload(self.manifest)
        for field in ("creative_market_title", "creative_market_description", "creative_market_keywords"):
            self.assertIn(field, payload, f"Missing Creative Market field: {field}")

    def test_payload_creative_market_keywords_is_list(self):
        payload = build_webhook_payload(self.manifest)
        self.assertIsInstance(payload["creative_market_keywords"], list)

    def test_payload_has_adobe_stock_fields(self):
        payload = build_webhook_payload(self.manifest)
        for field in ("adobe_stock_title", "adobe_stock_keywords", "adobe_stock_category"):
            self.assertIn(field, payload, f"Missing Adobe Stock field: {field}")

    def test_payload_adobe_keywords_string(self):
        payload = build_webhook_payload(self.manifest)
        self.assertIsInstance(payload["adobe_stock_keywords_string"], str)
        self.assertGreater(len(payload["adobe_stock_keywords_string"]), 0)

    def test_payload_has_gdrive_path(self):
        payload = build_webhook_payload(self.manifest)
        self.assertIn("gdrive_path", payload)
        self.assertIn("AI Art Packs", payload["gdrive_path"])

    def test_payload_has_marketplace_ready_flags(self):
        payload = build_webhook_payload(self.manifest)
        self.assertTrue(payload["marketplace_ready_etsy"])
        self.assertTrue(payload["marketplace_ready_creative_market"])
        self.assertTrue(payload["marketplace_ready_adobe_stock"])

    def test_payload_has_license_info(self):
        payload = build_webhook_payload(self.manifest)
        self.assertTrue(payload["license_commercial_use"])
        self.assertTrue(payload["ai_generated"])

    def test_payload_has_timestamps(self):
        payload = build_webhook_payload(self.manifest)
        self.assertIn("generated_at", payload)
        self.assertIn("sent_at", payload)

    def test_payload_success_is_true(self):
        payload = build_webhook_payload(self.manifest)
        self.assertTrue(payload["success"])

    def test_payload_serializable_to_json(self):
        payload = build_webhook_payload(self.manifest)
        try:
            json_str = json.dumps(payload)
            self.assertGreater(len(json_str), 100)
        except (TypeError, ValueError) as e:
            self.fail(f"Payload not JSON-serializable: {e}")


class TestBase64Encoding(unittest.TestCase):
    def test_small_zip_gets_encoded(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(b"PK" + b"\x00" * 100)
            zip_path = Path(f.name)
        try:
            result = encode_zip_base64(zip_path)
            self.assertIsNotNone(result)
            self.assertIsInstance(result, str)
            self.assertGreater(len(result), 0)
        finally:
            zip_path.unlink()

    def test_large_zip_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            large_zip = Path(tmpdir) / "large.zip"
            large_zip.write_bytes(b"\x00" * (11 * 1024 * 1024))
            result = encode_zip_base64(large_zip)
            self.assertIsNone(result)


class TestWebhookSending(unittest.TestCase):
    def setUp(self):
        self.manifest = make_sample_manifest()
        self.payload = build_webhook_payload(self.manifest)

    def test_skips_unconfigured_webhook(self):
        result = send_to_webhook(
            webhook_url="${ZAPIER_WEBHOOK_URL}",
            payload=self.payload,
            webhook_name="test_webhook",
        )
        self.assertFalse(result["success"])
        self.assertTrue(result.get("skipped"))
        self.assertEqual(result["reason"], "url_not_configured")

    def test_skips_empty_url(self):
        result = send_to_webhook(
            webhook_url="",
            payload=self.payload,
            webhook_name="empty_webhook",
        )
        self.assertFalse(result["success"])
        self.assertTrue(result.get("skipped"))

    @patch("scripts.send_to_webhook.requests.post")
    def test_successful_send(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = send_to_webhook(
            webhook_url="https://hooks.zapier.com/hooks/catch/fake/abc123/",
            payload=self.payload,
            webhook_name="test_success",
            retry_attempts=1,
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["status_code"], 200)
        mock_post.assert_called_once()

    @patch("scripts.send_to_webhook.requests.post")
    def test_retries_on_connection_error(self, mock_post):
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("refused")

        result = send_to_webhook(
            webhook_url="https://hooks.zapier.com/hooks/catch/fake/xyz/",
            payload=self.payload,
            webhook_name="retry_test",
            retry_attempts=2,
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "max_retries_exceeded")
        self.assertEqual(mock_post.call_count, 2)

    @patch("scripts.send_to_webhook.requests.post")
    def test_sends_correct_payload_fields(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ok"
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        send_to_webhook(
            webhook_url="https://hooks.zapier.com/hooks/catch/fake/verify/",
            payload=self.payload,
            webhook_name="field_verify",
            retry_attempts=1,
        )

        call_kwargs = mock_post.call_args
        sent_json = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
        self.assertIn("etsy_title", sent_json)
        self.assertIn("etsy_tags", sent_json)
        self.assertIn("adobe_stock_keywords", sent_json)

    @patch("scripts.send_to_webhook.requests.post")
    def test_http_error_no_retry(self, mock_post):
        import requests as req_module
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        http_error = req_module.exceptions.HTTPError(response=mock_response)
        mock_post.return_value = mock_response
        mock_response.raise_for_status.side_effect = http_error

        result = send_to_webhook(
            webhook_url="https://hooks.zapier.com/hooks/catch/fake/badreq/",
            payload=self.payload,
            webhook_name="http_error_test",
            retry_attempts=3,
        )
        self.assertFalse(result["success"])
        self.assertEqual(mock_post.call_count, 1)


class TestSEOContentQuality(unittest.TestCase):
    """Validate the SEO output meets marketplace requirements."""

    def setUp(self):
        self.config = load_config()
        self.manifest = make_sample_manifest(50)
        self.payload = build_webhook_payload(self.manifest)

    def test_etsy_title_length(self):
        max_chars = self.config["seo"]["title_max_chars"]
        self.assertLessEqual(len(self.payload["etsy_title"]), max_chars)

    def test_etsy_tags_count(self):
        self.assertEqual(len(self.payload["etsy_tags"]), 13)

    def test_etsy_tags_max_length(self):
        max_chars = self.config["seo"]["etsy_tag_max_chars"]
        for tag in self.payload["etsy_tags"]:
            self.assertLessEqual(len(tag), max_chars, f"Tag too long: '{tag}'")

    def test_etsy_price_is_positive(self):
        self.assertGreater(self.payload["etsy_price_usd"], 0)

    def test_adobe_stock_keywords_count(self):
        kw_count = len(self.payload["adobe_stock_keywords"])
        max_kw = self.config["seo"]["adobe_stock_keywords_count"]
        self.assertLessEqual(kw_count, max_kw)
        self.assertGreater(kw_count, 0)

    def test_creative_market_keywords_is_list(self):
        self.assertIsInstance(self.payload["creative_market_keywords"], list)
        self.assertGreater(len(self.payload["creative_market_keywords"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
