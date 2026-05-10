#!/usr/bin/env python3
"""
POSTs ZIP + metadata payload to configured Zapier webhooks.
Supports multiple webhook targets with retry logic.
"""

import os
import sys
import json
import time
import base64
import logging
import requests
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.config_loader import load_config, load_webhooks

logger = setup_logger("send_to_webhook")

MAX_BASE64_SIZE_MB = 10


def load_manifest(theme: str, config: dict) -> dict:
    output_base = PROJECT_ROOT / config["output"]["base_dir"]
    manifest_path = output_base / theme / config["output"]["manifest_filename"]
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text())


def encode_zip_base64(zip_path: Path) -> Optional[str]:
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_BASE64_SIZE_MB:
        logger.warning(
            f"ZIP too large for base64 encoding ({size_mb:.1f}MB > {MAX_BASE64_SIZE_MB}MB). "
            "Will send metadata only; use Google Drive for the file."
        )
        return None
    return base64.b64encode(zip_path.read_bytes()).decode("utf-8")


def build_webhook_payload(manifest: dict, zip_path: Optional[Path] = None) -> dict:
    seo = manifest["seo"]
    etsy_seo = seo["etsy"]
    cm_seo = seo["creative_market"]
    adobe_seo = seo["adobe_stock"]

    zip_base64 = None
    zip_info = manifest["files"].get("zip", {})

    if zip_path and zip_path.exists():
        zip_base64 = encode_zip_base64(zip_path)
    elif zip_info.get("path"):
        actual_zip = PROJECT_ROOT / zip_info["path"]
        if actual_zip.exists():
            zip_base64 = encode_zip_base64(actual_zip)

    adobe_first = adobe_seo[0] if adobe_seo else {}

    payload = {
        "pack_id": manifest["pack_id"],
        "run_id": manifest["run_id"],
        "theme": manifest["pack"]["theme"],
        "style": manifest["pack"]["style"],
        "theme_display": manifest["pack"]["theme_display"],
        "style_display": manifest["pack"]["style_display"],
        "image_count": manifest["pack"]["image_count"],
        "generated_at": manifest["generated_at"],
        "sent_at": datetime.now(timezone.utc).isoformat(),

        "zip_filename": zip_info.get("filename", ""),
        "zip_size_mb": zip_info.get("size_mb", 0),
        "zip_base64": zip_base64 or "",
        "zip_base64_available": zip_base64 is not None,

        "gdrive_path": manifest["files"].get("gdrive_path", ""),

        "etsy_title": etsy_seo["title"],
        "etsy_description": etsy_seo["description"],
        "etsy_tags": etsy_seo["tags"],
        "etsy_tags_string": ", ".join(etsy_seo["tags"]),
        "etsy_price_usd": etsy_seo["price_usd"],
        "etsy_category": etsy_seo["category"],

        "creative_market_title": cm_seo["title"],
        "creative_market_description": cm_seo["description"],
        "creative_market_keywords": cm_seo["keywords"],
        "creative_market_keywords_string": ", ".join(cm_seo["keywords"]),

        "adobe_stock_title": adobe_first.get("title", ""),
        "adobe_stock_keywords": adobe_first.get("keywords", []),
        "adobe_stock_keywords_string": ", ".join(adobe_first.get("keywords", [])),
        "adobe_stock_category": adobe_first.get("category", ""),

        "marketplace_ready_etsy": manifest["marketplace_ready"]["etsy"],
        "marketplace_ready_creative_market": manifest["marketplace_ready"]["creative_market"],
        "marketplace_ready_adobe_stock": manifest["marketplace_ready"]["adobe_stock"],

        "license_commercial_use": manifest["license"]["commercial_use"],
        "ai_generated": manifest["license"]["ai_generated"],
        "ai_disclosure": manifest["license"]["ai_disclosure"],

        "success": True,
    }

    return payload


def send_to_webhook(
    webhook_url: str,
    payload: dict,
    webhook_name: str = "webhook",
    retry_attempts: int = 3,
    timeout: int = 30,
) -> dict:
    if not webhook_url or webhook_url.startswith("${"):
        logger.warning(f"Webhook {webhook_name} URL not configured (placeholder found). Skipping.")
        return {
            "webhook": webhook_name,
            "success": False,
            "reason": "url_not_configured",
            "skipped": True,
        }

    for attempt in range(1, retry_attempts + 1):
        try:
            logger.info(f"Sending to {webhook_name} (attempt {attempt}/{retry_attempts})")
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json", "User-Agent": "AIArtPackGenerator/1.0"},
            )
            response.raise_for_status()

            logger.info(f"Webhook {webhook_name} success: HTTP {response.status_code}")
            return {
                "webhook": webhook_name,
                "success": True,
                "status_code": response.status_code,
                "response": response.text[:500],
                "attempt": attempt,
            }

        except requests.exceptions.Timeout:
            logger.warning(f"Webhook {webhook_name} timed out (attempt {attempt})")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Webhook {webhook_name} connection error (attempt {attempt}): {e}")
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"Webhook {webhook_name} HTTP error: {e.response.status_code} - {e.response.text[:200]}"
            )
            return {
                "webhook": webhook_name,
                "success": False,
                "status_code": e.response.status_code,
                "error": str(e),
                "attempt": attempt,
            }
        except Exception as e:
            logger.error(f"Webhook {webhook_name} unexpected error: {e}")

        if attempt < retry_attempts:
            wait = 2 ** attempt
            logger.info(f"Retrying in {wait}s...")
            time.sleep(wait)

    return {
        "webhook": webhook_name,
        "success": False,
        "reason": "max_retries_exceeded",
        "attempt": retry_attempts,
    }


def send_all_webhooks(theme: str, config: dict, zip_path: Optional[Path] = None) -> list[dict]:
    manifest = load_manifest(theme, config)
    webhooks_config = load_webhooks()
    zapier_webhooks = webhooks_config.get("zapier", {})

    payload = build_webhook_payload(manifest, zip_path)
    logger.info(
        f"Sending pack '{theme}' to webhooks | "
        f"pack_id={payload['pack_id']} | images={payload['image_count']}"
    )

    results = []
    for wh_key, wh_config in zapier_webhooks.items():
        if wh_key == "_comment" or wh_key == "_instructions":
            continue
        if not wh_config.get("active", False):
            logger.info(f"Skipping inactive webhook: {wh_key}")
            results.append({"webhook": wh_key, "success": True, "skipped": True, "reason": "inactive"})
            continue

        url = os.environ.get(
            f"ZAPIER_{wh_key.upper()}_URL",
            wh_config.get("url", ""),
        )
        result = send_to_webhook(
            webhook_url=url,
            payload=payload,
            webhook_name=wh_key,
            retry_attempts=wh_config.get("retry_attempts", 3),
            timeout=wh_config.get("timeout_seconds", 30),
        )
        results.append(result)

    successful = sum(1 for r in results if r.get("success") and not r.get("skipped"))
    skipped = sum(1 for r in results if r.get("skipped"))
    failed = sum(1 for r in results if not r.get("success") and not r.get("skipped"))
    logger.info(f"Webhook sending complete: {successful} sent, {skipped} skipped, {failed} failed")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Send art pack to Zapier webhooks")
    parser.add_argument("--theme", required=True)
    parser.add_argument("--zip-path", help="Path to the ZIP file")
    args = parser.parse_args()

    config = load_config()
    zip_p = Path(args.zip_path) if args.zip_path else None
    results = send_all_webhooks(args.theme, config, zip_p)
    print(json.dumps(results, indent=2))
    failed = any(not r.get("success") and not r.get("skipped") for r in results)
    sys.exit(1 if failed else 0)
