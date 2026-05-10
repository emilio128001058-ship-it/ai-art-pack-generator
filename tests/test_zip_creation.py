#!/usr/bin/env python3
"""
Tests for ZIP creation logic.
Covers folder zipping, file inclusion, README generation, and error handling.
"""

import sys
import json
import zipfile
import unittest
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.prepare_zip import zip_theme_folder, zip_all_themes
from utils.config_loader import load_config


def make_fake_theme_dir(base_dir: Path, theme: str, image_count: int = 5) -> Path:
    theme_dir = base_dir / theme
    theme_dir.mkdir(parents=True, exist_ok=True)
    for i in range(image_count):
        img = theme_dir / f"{theme}_watercolor_{i+1:03d}.png"
        img.write_bytes(b"PNG" + bytes([i] * 100))
    return theme_dir


class TestZipThemeFolder(unittest.TestCase):
    def test_zip_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            theme_dir = make_fake_theme_dir(base, "test_theme")
            zips_dir = base / "zips"
            result = zip_theme_folder(theme_dir, zips_dir)
            self.assertTrue(result["success"])
            self.assertTrue(Path(result["zip_path"]).exists())

    def test_zip_contains_all_images(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            theme_dir = make_fake_theme_dir(base, "img_test", image_count=7)
            zips_dir = base / "zips"
            result = zip_theme_folder(theme_dir, zips_dir)
            self.assertTrue(result["success"])

            with zipfile.ZipFile(result["zip_path"], "r") as zf:
                names = zf.namelist()
            png_count = sum(1 for n in names if n.endswith(".png"))
            self.assertEqual(png_count, 7)

    def test_zip_excludes_keep_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            theme_dir = make_fake_theme_dir(base, "keep_test")
            (theme_dir / ".keep").touch()
            zips_dir = base / "zips"
            result = zip_theme_folder(theme_dir, zips_dir)
            self.assertTrue(result["success"])

            with zipfile.ZipFile(result["zip_path"], "r") as zf:
                names = zf.namelist()
            self.assertNotIn(".keep", names)

    def test_zip_includes_readme(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            theme_dir = make_fake_theme_dir(base, "readme_test")
            zips_dir = base / "zips"
            result = zip_theme_folder(theme_dir, zips_dir)
            self.assertTrue(result["success"])

            with zipfile.ZipFile(result["zip_path"], "r") as zf:
                names = zf.namelist()
            self.assertIn("README.txt", names)

    def test_zip_readme_contains_license(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            theme_dir = make_fake_theme_dir(base, "license_test")
            zips_dir = base / "zips"
            result = zip_theme_folder(theme_dir, zips_dir)

            with zipfile.ZipFile(result["zip_path"], "r") as zf:
                readme = zf.read("README.txt").decode("utf-8")
            self.assertIn("Commercial use", readme)
            self.assertIn("Personal use", readme)

    def test_zip_result_has_size_info(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            theme_dir = make_fake_theme_dir(base, "size_test")
            zips_dir = base / "zips"
            result = zip_theme_folder(theme_dir, zips_dir)
            self.assertTrue(result["success"])
            self.assertIn("zip_size_bytes", result)
            self.assertIn("zip_size_mb", result)
            self.assertIn("files_included", result)
            self.assertGreater(result["zip_size_bytes"], 0)

    def test_zip_result_has_correct_file_count(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            theme_dir = make_fake_theme_dir(base, "count_test", image_count=10)
            zips_dir = base / "zips"
            result = zip_theme_folder(theme_dir, zips_dir)
            self.assertEqual(result["files_included"], 10)

    def test_zip_empty_folder_returns_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            empty_dir = base / "empty_theme"
            empty_dir.mkdir()
            (empty_dir / ".keep").touch()
            zips_dir = base / "zips"
            result = zip_theme_folder(empty_dir, zips_dir)
            self.assertFalse(result["success"])
            self.assertEqual(result["reason"], "no_files")

    def test_zip_creates_zips_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            theme_dir = make_fake_theme_dir(base, "dir_test")
            zips_dir = base / "zips" / "new_subdir"
            result = zip_theme_folder(theme_dir, zips_dir)
            self.assertTrue(result["success"])
            self.assertTrue(zips_dir.exists())

    def test_zip_includes_manifest_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            theme_dir = make_fake_theme_dir(base, "manifest_test")
            manifest = {"theme": "manifest_test", "image_count": 5}
            (theme_dir / "manifest.json").write_text(json.dumps(manifest))
            zips_dir = base / "zips"
            result = zip_theme_folder(theme_dir, zips_dir, include_manifest=True)

            with zipfile.ZipFile(result["zip_path"], "r") as zf:
                names = zf.namelist()
            self.assertIn("manifest.json", names)

    def test_zip_filename_contains_theme_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            theme_dir = make_fake_theme_dir(base, "naming_test")
            zips_dir = base / "zips"
            result = zip_theme_folder(theme_dir, zips_dir)
            self.assertIn("naming_test", result["zip_filename"])

    def test_zip_is_valid_zip_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            theme_dir = make_fake_theme_dir(base, "valid_test")
            zips_dir = base / "zips"
            result = zip_theme_folder(theme_dir, zips_dir)
            self.assertTrue(zipfile.is_zipfile(result["zip_path"]))


class TestZipAllThemes(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def test_zip_all_returns_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            make_fake_theme_dir(base, "theme_a")
            make_fake_theme_dir(base, "theme_b")
            config = dict(self.config)
            config["output"] = dict(config["output"])
            config["output"]["zips_dir"] = str(base / "zips")
            results = zip_all_themes(base, config)
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 2)

    def test_zip_all_skips_zips_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            make_fake_theme_dir(base, "theme_c")
            (base / "zips").mkdir()
            config = dict(self.config)
            config["output"] = dict(config["output"])
            config["output"]["zips_dir"] = str(base / "zips")
            results = zip_all_themes(base, config)
            theme_names = [r["theme"] for r in results]
            self.assertNotIn("zips", theme_names)

    def test_zip_all_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = dict(self.config)
            config["output"] = dict(config["output"])
            config["output"]["zips_dir"] = str(Path(tmpdir) / "zips")
            results = zip_all_themes(Path(tmpdir), config)
            self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
