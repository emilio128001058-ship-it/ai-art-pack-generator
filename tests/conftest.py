"""
Pytest configuration and shared fixtures.
"""

import sys
import pytest
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root():
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def config():
    from utils.config_loader import load_config
    return load_config()


@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_theme_dir(temp_output_dir):
    theme_dir = temp_output_dir / "test_theme"
    theme_dir.mkdir()
    for i in range(5):
        (theme_dir / f"test_theme_watercolor_{i+1:03d}.png").write_bytes(
            b"PNG" + bytes([i] * 50)
        )
    return theme_dir


@pytest.fixture
def sample_manifest():
    import uuid
    from datetime import datetime, timezone
    return {
        "pack_id": str(uuid.uuid4()),
        "run_id": str(uuid.uuid4()),
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pack": {
            "theme": "cosmic_nebula",
            "style": "watercolor",
            "image_count": 50,
            "theme_display": "Cosmic Nebula",
            "style_display": "Watercolor",
        },
        "files": {
            "images": [],
            "zip": {
                "filename": "cosmic_nebula_test.zip",
                "path": "output/zips/cosmic_nebula_test.zip",
                "size_bytes": 1024 * 1024 * 5,
                "size_mb": 5.0,
                "sha256": "abc123",
            },
            "gdrive_path": "AI Art Packs/2024-01/cosmic_nebula",
        },
        "seo": {
            "etsy": {
                "title": "Cosmic Nebula Watercolor Digital Art Pack | 50 Images | Commercial Use",
                "description": "Beautiful cosmic nebula art...",
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
                "title": "50 Cosmic Nebula Watercolor Backgrounds Bundle",
                "description": "Premium cosmic nebula backgrounds...",
                "keywords": [
                    "cosmic", "nebula", "space", "watercolor", "backgrounds",
                    "digital", "commercial", "high resolution", "PNG", "bundle",
                    "galaxy", "stars", "universe", "astronomy", "abstract",
                ],
            },
            "adobe_stock": [
                {
                    "title": "Cosmic nebula watercolor - ethereal digital background",
                    "keywords": ["cosmic", "nebula", "space", "watercolor", "background"],
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
