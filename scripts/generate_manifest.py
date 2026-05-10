#!/usr/bin/env python3
"""
Creates manifest.json for a completed art pack with full metadata,
SEO content, image list, and marketplace listing data.
"""

import sys
import json
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.config_loader import load_config
from scripts.generate_seo import generate_seo_package

logger = setup_logger("generate_manifest")


def compute_file_hash(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_image_list(theme_dir: Path) -> list[dict]:
    images = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        for img_path in sorted(theme_dir.glob(ext)):
            if img_path.name == ".keep":
                continue
            stat = img_path.stat()
            images.append({
                "filename": img_path.name,
                "path": str(img_path.relative_to(PROJECT_ROOT)),
                "size_bytes": stat.st_size,
                "size_kb": round(stat.st_size / 1024, 2),
                "sha256": compute_file_hash(img_path),
            })
    return images


def generate_manifest(
    theme: str,
    style: str,
    run_id: str,
    zip_path: Optional[Path] = None,
    config: dict = None,
) -> dict:
    if config is None:
        config = load_config()

    output_base = PROJECT_ROOT / config["output"]["base_dir"]
    theme_dir = output_base / theme

    if not theme_dir.exists():
        raise FileNotFoundError(f"Theme directory not found: {theme_dir}")

    images = get_image_list(theme_dir)
    image_count = len(images)

    if image_count == 0:
        raise ValueError(f"No images found in {theme_dir}")

    seo = generate_seo_package(theme, style, image_count, config)

    zip_info = {}
    if zip_path and zip_path.exists():
        stat = zip_path.stat()
        zip_info = {
            "filename": zip_path.name,
            "path": str(zip_path.relative_to(PROJECT_ROOT)),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "sha256": compute_file_hash(zip_path),
        }

    gdrive_path = (
        f"{config['google_drive']['upload_folder']}/"
        f"{datetime.now().strftime('%Y-%m')}/"
        f"{theme}"
    )

    manifest = {
        "pack_id": str(uuid.uuid4()),
        "run_id": run_id,
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),

        "pack": {
            "theme": theme,
            "style": style,
            "image_count": image_count,
            "theme_display": theme.replace("_", " ").title(),
            "style_display": style.replace("_", " ").title(),
        },

        "files": {
            "images": images,
            "zip": zip_info,
            "gdrive_path": gdrive_path,
        },

        "seo": seo,

        "marketplace_ready": {
            "etsy": bool(seo["etsy"]["title"] and seo["etsy"]["tags"]),
            "creative_market": bool(seo["creative_market"]["title"]),
            "adobe_stock": bool(seo["adobe_stock"]),
        },

        "license": {
            "type": "Commercial Use",
            "personal_use": True,
            "commercial_use": True,
            "resale_of_files": False,
            "attribution_required": False,
            "ai_generated": True,
            "ai_disclosure": "Images generated using AI (DALL-E or Stable Diffusion)",
        },

        "config_snapshot": {
            "provider": config["image_generation"]["provider"],
            "model": config["image_generation"]["model"],
            "image_size": config["image_generation"]["image_size"],
            "quality": config["image_generation"]["quality"],
        },
    }

    manifest_path = theme_dir / config["output"]["manifest_filename"]
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.info(f"Manifest saved: {manifest_path}")

    return manifest


# Allow Optional import without adding it to sys.path issues
from typing import Optional


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate manifest for an art pack")
    parser.add_argument("--theme", required=True)
    parser.add_argument("--style", required=True)
    parser.add_argument("--run-id", default=str(uuid.uuid4()))
    parser.add_argument("--zip-path", help="Path to the ZIP file")
    args = parser.parse_args()

    zip_p = Path(args.zip_path) if args.zip_path else None
    manifest = generate_manifest(args.theme, args.style, args.run_id, zip_p)
    print(json.dumps(manifest, indent=2))
