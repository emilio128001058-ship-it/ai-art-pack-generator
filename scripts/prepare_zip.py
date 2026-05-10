#!/usr/bin/env python3
"""
Zips each theme folder in output/ into output/zips/<theme>.zip.
Skips .keep files and non-image files.
"""

import sys
import json
import zipfile
import logging
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.config_loader import load_config

logger = setup_logger("prepare_zip")

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tiff", ".bmp"}


def zip_theme_folder(
    theme_dir: Path,
    zip_output_dir: Path,
    include_manifest: bool = True,
    max_size_mb: int = 500,
) -> dict:
    theme_name = theme_dir.name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{theme_name}_{timestamp}.zip"
    zip_path = zip_output_dir / zip_filename

    zip_output_dir.mkdir(parents=True, exist_ok=True)

    files_to_zip = []
    for f in sorted(theme_dir.iterdir()):
        if f.name == ".keep":
            continue
        if f.suffix.lower() in IMAGE_EXTENSIONS:
            files_to_zip.append(f)
        elif include_manifest and f.name == "manifest.json":
            files_to_zip.append(f)

    if not files_to_zip:
        logger.warning(f"No files to zip in {theme_dir}")
        return {"success": False, "reason": "no_files", "theme": theme_name}

    total_size = sum(f.stat().st_size for f in files_to_zip)
    total_size_mb = total_size / (1024 * 1024)

    if total_size_mb > max_size_mb:
        logger.warning(
            f"Pack size {total_size_mb:.1f}MB exceeds max {max_size_mb}MB, "
            f"will split into parts"
        )

    logger.info(
        f"Zipping {len(files_to_zip)} files ({total_size_mb:.1f}MB) → {zip_path}"
    )

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for file_path in files_to_zip:
                arcname = file_path.name
                zf.write(file_path, arcname)
                logger.debug(f"  Added: {arcname}")

            readme_content = f"""AI Art Pack — {theme_name.replace('_', ' ').title()}
{'=' * 50}

This pack contains {len([f for f in files_to_zip if f.suffix.lower() in IMAGE_EXTENSIONS])} high-resolution AI-generated images.

LICENSE:
- Personal use: Allowed
- Commercial use: Allowed (products, client work, resale of products)
- Resale of original files: NOT allowed
- Attribution: Not required

AI DISCLOSURE:
Images in this pack were generated using AI image generation technology.

For support, please contact the seller.

Generated: {datetime.now().strftime('%Y-%m-%d')}
"""
            zf.writestr("README.txt", readme_content)

        zip_stat = zip_path.stat()
        result = {
            "success": True,
            "theme": theme_name,
            "zip_path": str(zip_path),
            "zip_filename": zip_filename,
            "files_included": len(files_to_zip),
            "original_size_mb": round(total_size_mb, 2),
            "zip_size_bytes": zip_stat.st_size,
            "zip_size_mb": round(zip_stat.st_size / (1024 * 1024), 2),
            "compression_ratio": round(zip_stat.st_size / total_size, 3) if total_size > 0 else 0,
        }
        logger.info(
            f"ZIP created: {zip_filename} "
            f"({result['zip_size_mb']:.1f}MB, ratio={result['compression_ratio']:.2f})"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to create ZIP for {theme_name}: {e}")
        if zip_path.exists():
            zip_path.unlink()
        return {"success": False, "reason": str(e), "theme": theme_name}


def zip_all_themes(output_dir: Path, config: dict) -> list[dict]:
    zips_dir = PROJECT_ROOT / config["output"]["zips_dir"]
    max_size = config["output"]["max_zip_size_mb"]
    results = []

    theme_dirs = [
        d for d in sorted(output_dir.iterdir())
        if d.is_dir() and d.name != "zips" and not d.name.startswith(".")
    ]

    if not theme_dirs:
        logger.warning(f"No theme directories found in {output_dir}")
        return results

    logger.info(f"Found {len(theme_dirs)} theme(s) to zip")

    for theme_dir in theme_dirs:
        result = zip_theme_folder(theme_dir, zips_dir, max_size_mb=max_size)
        results.append(result)

    successful = sum(1 for r in results if r.get("success"))
    logger.info(f"Zipping complete: {successful}/{len(results)} succeeded")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Zip art pack theme folders")
    parser.add_argument("--theme", help="Zip only this specific theme")
    parser.add_argument("--output-dir", help="Override output directory")
    args = parser.parse_args()

    config = load_config()
    output_base = Path(args.output_dir or PROJECT_ROOT / config["output"]["base_dir"])

    if args.theme:
        theme_dir = output_base / args.theme
        if not theme_dir.exists():
            logger.error(f"Theme directory not found: {theme_dir}")
            sys.exit(1)
        zips_dir = PROJECT_ROOT / config["output"]["zips_dir"]
        results = [zip_theme_folder(theme_dir, zips_dir)]
    else:
        results = zip_all_themes(output_base, config)

    print(json.dumps(results, indent=2))
    failed = any(not r.get("success") for r in results)
    sys.exit(1 if failed else 0)
