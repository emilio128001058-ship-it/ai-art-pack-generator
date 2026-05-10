#!/usr/bin/env python3
"""
Tests for image generation logic.
Covers prompt building, file saving, and pack generation with dry-run mode.
"""

import sys
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_images import (
    build_prompt,
    load_themes,
    load_styles,
    save_image,
    generate_pack,
)
from utils.config_loader import load_config


class TestPromptBuilding(unittest.TestCase):
    def test_build_prompt_returns_string(self):
        prompt = build_prompt("cosmic_nebula", "watercolor", 0, "")
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 10)

    def test_build_prompt_contains_theme(self):
        prompt = build_prompt("cosmic_nebula", "watercolor", 0, "")
        self.assertIn("Cosmic Nebula", prompt)

    def test_build_prompt_contains_style(self):
        prompt = build_prompt("cosmic_nebula", "watercolor", 0, "")
        self.assertIn("watercolor", prompt)

    def test_build_prompt_varies_with_index(self):
        prompts = [build_prompt("cosmic_nebula", "watercolor", i, "") for i in range(8)]
        unique_starters = len(set(p.split(",")[0] for p in prompts))
        self.assertGreater(unique_starters, 1, "Prompts should vary by index")

    def test_build_prompt_has_quality_tags(self):
        prompt = build_prompt("enchanted_forest", "oil painting", 0, "")
        self.assertIn("masterpiece", prompt)

    def test_build_prompt_no_watermark_instruction(self):
        prompt = build_prompt("dragon_lair", "fantasy concept art", 0, "")
        self.assertIn("no watermarks", prompt)


class TestFileLoading(unittest.TestCase):
    def setUp(self):
        self.themes_path = PROJECT_ROOT / "prompts" / "themes.txt"
        self.styles_path = PROJECT_ROOT / "prompts" / "styles.txt"

    def test_themes_file_exists(self):
        self.assertTrue(self.themes_path.exists(), "themes.txt must exist")

    def test_styles_file_exists(self):
        self.assertTrue(self.styles_path.exists(), "styles.txt must exist")

    def test_load_themes_returns_list(self):
        themes = load_themes(self.themes_path)
        self.assertIsInstance(themes, list)
        self.assertGreater(len(themes), 0)

    def test_load_themes_no_empty_strings(self):
        themes = load_themes(self.themes_path)
        for t in themes:
            self.assertTrue(t.strip(), f"Empty theme found: '{t}'")

    def test_load_themes_no_comments(self):
        themes = load_themes(self.themes_path)
        for t in themes:
            self.assertFalse(t.startswith("#"), f"Comment leaked into themes: '{t}'")

    def test_load_styles_returns_list(self):
        styles = load_styles(self.styles_path)
        self.assertIsInstance(styles, list)
        self.assertGreater(len(styles), 0)

    def test_load_styles_no_empty_strings(self):
        styles = load_styles(self.styles_path)
        for s in styles:
            self.assertTrue(s.strip())

    def test_themes_count_reasonable(self):
        themes = load_themes(self.themes_path)
        self.assertGreaterEqual(len(themes), 10, "Should have at least 10 themes")

    def test_styles_count_reasonable(self):
        styles = load_styles(self.styles_path)
        self.assertGreaterEqual(len(styles), 5, "Should have at least 5 styles")


class TestImageSaving(unittest.TestCase):
    def test_save_image_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.png"
            result = save_image(b"FAKE_IMAGE_DATA", output_path)
            self.assertTrue(result)
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_bytes(), b"FAKE_IMAGE_DATA")

    def test_save_image_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "test.png"
            result = save_image(b"DATA", output_path)
            self.assertTrue(result)
            self.assertTrue(output_path.exists())

    def test_save_image_returns_false_on_error(self):
        invalid_path = Path("/nonexistent/readonly/path/test.png")
        result = save_image(b"DATA", invalid_path)
        self.assertFalse(result)


class TestPackGeneration(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_dry_run_generates_placeholders(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = generate_pack(
                theme="test_theme",
                style="watercolor",
                image_count=5,
                output_dir=output_dir,
                config=self.config,
                dry_run=True,
            )
            self.assertEqual(result["generated"], 5)
            self.assertEqual(result["failed"], 0)
            self.assertEqual(len(result["images"]), 5)

    def test_dry_run_creates_output_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_pack(
                theme="new_theme",
                style="watercolor",
                image_count=3,
                output_dir=output_dir,
                config=self.config,
                dry_run=True,
            )
            theme_dir = output_dir / "new_theme"
            self.assertTrue(theme_dir.exists())

    def test_dry_run_creates_correct_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for count in [1, 5, 10]:
                result = generate_pack(
                    theme=f"theme_{count}",
                    style="watercolor",
                    image_count=count,
                    output_dir=Path(tmpdir),
                    config=self.config,
                    dry_run=True,
                )
                self.assertEqual(result["generated"], count)

    def test_dry_run_result_has_required_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generate_pack(
                theme="test",
                style="watercolor",
                image_count=2,
                output_dir=Path(tmpdir),
                config=self.config,
                dry_run=True,
            )
            for key in ("theme", "style", "generated", "failed", "images"):
                self.assertIn(key, result, f"Missing key: {key}")

    def test_dry_run_skips_existing_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            # First run
            generate_pack("skip_test", "watercolor", 3, output_dir, self.config, dry_run=True)
            # Second run should skip existing
            result = generate_pack("skip_test", "watercolor", 3, output_dir, self.config, dry_run=True)
            self.assertEqual(result["generated"], 3)
            self.assertEqual(result["failed"], 0)


class TestConfigValidation(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_config_has_image_generation(self):
        self.assertIn("image_generation", self.config)

    def test_config_has_images_per_pack(self):
        self.assertIn("images_per_pack", self.config["image_generation"])
        ipp = self.config["image_generation"]["images_per_pack"]
        self.assertIn("min", ipp)
        self.assertIn("max", ipp)

    def test_config_min_less_than_max(self):
        ipp = self.config["image_generation"]["images_per_pack"]
        self.assertLess(ipp["min"], ipp["max"])

    def test_config_has_valid_provider(self):
        provider = self.config["image_generation"]["provider"]
        self.assertIn(provider, ["openai", "stability"])

    def test_config_has_output_section(self):
        self.assertIn("output", self.config)
        self.assertIn("base_dir", self.config["output"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
