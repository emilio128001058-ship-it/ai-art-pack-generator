#!/usr/bin/env python3
"""
Clears output/<theme>/ directories after successful packaging.
Preserves .keep files and the zips/ directory.
"""

import sys
import shutil
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.config_loader import load_config

logger = setup_logger("cleanup")

PRESERVE_NAMES = {".keep", "zips"}
PRESERVE_EXTENSIONS = {".keep"}


def cleanup_theme(theme_dir: Path, keep_manifest: bool = False) -> dict:
    if not theme_dir.exists():
        return {"theme": theme_dir.name, "success": True, "removed": 0, "skipped": 0}

    removed = 0
    skipped = 0

    for item in list(theme_dir.iterdir()):
        if item.name in PRESERVE_NAMES or item.suffix in PRESERVE_EXTENSIONS:
            skipped += 1
            continue
        if keep_manifest and item.name == "manifest.json":
            skipped += 1
            continue

        try:
            if item.is_file():
                item.unlink()
                removed += 1
                logger.debug(f"Removed file: {item}")
            elif item.is_dir():
                shutil.rmtree(item)
                removed += 1
                logger.debug(f"Removed directory: {item}")
        except Exception as e:
            logger.warning(f"Could not remove {item}: {e}")
            skipped += 1

    logger.info(f"Cleaned {theme_dir.name}: {removed} removed, {skipped} preserved")
    return {
        "theme": theme_dir.name,
        "success": True,
        "removed": removed,
        "skipped": skipped,
    }


def cleanup_all(output_dir: Path, keep_manifest: bool = True) -> list[dict]:
    results = []

    if not output_dir.exists():
        logger.warning(f"Output directory does not exist: {output_dir}")
        return results

    theme_dirs = [
        d for d in sorted(output_dir.iterdir())
        if d.is_dir() and d.name not in PRESERVE_NAMES and not d.name.startswith(".")
    ]

    if not theme_dirs:
        logger.info("No theme directories found to clean")
        return results

    for theme_dir in theme_dirs:
        result = cleanup_theme(theme_dir, keep_manifest)
        results.append(result)

    total_removed = sum(r["removed"] for r in results)
    logger.info(f"Cleanup complete: {total_removed} files removed across {len(results)} themes")
    return results


def cleanup_logs(logs_dir: Path, keep_count: int = 10) -> int:
    if not logs_dir.exists():
        return 0

    log_files = sorted(logs_dir.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
    removed = 0
    for old_log in log_files[keep_count:]:
        old_log.unlink()
        removed += 1
        logger.debug(f"Removed old log: {old_log}")
    return removed


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Clean up output directories after zipping")
    parser.add_argument("--theme", help="Clean only this specific theme")
    parser.add_argument("--keep-manifest", action="store_true", default=True,
                        help="Keep manifest.json after cleanup")
    parser.add_argument("--clean-logs", action="store_true", help="Also clean old log files")
    parser.add_argument("--output-dir", help="Override output directory")
    args = parser.parse_args()

    config = load_config()
    output_base = Path(args.output_dir or PROJECT_ROOT / config["output"]["base_dir"])

    if args.theme:
        theme_dir = output_base / args.theme
        results = [cleanup_theme(theme_dir, args.keep_manifest)]
    else:
        results = cleanup_all(output_base, args.keep_manifest)

    if args.clean_logs:
        logs_dir = PROJECT_ROOT / config["output"]["logs_dir"]
        logs_removed = cleanup_logs(logs_dir)
        logger.info(f"Removed {logs_removed} old log files")

    print(json.dumps(results, indent=2))
    sys.exit(0)
