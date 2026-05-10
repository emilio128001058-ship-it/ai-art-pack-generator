#!/usr/bin/env python3
"""
Main automation orchestrator. Runs the full pipeline:
  1. Select random theme + style
  2. Generate images
  3. Generate manifest
  4. Zip the pack
  5. Send to Zapier webhooks
  6. Clean up output
  7. Log results
"""

import os
import sys
import json
import uuid
import random
import logging
import argparse
import traceback
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger, setup_run_logger
from utils.config_loader import load_config

logger = setup_logger("run_automation")


def load_themes() -> list[str]:
    path = PROJECT_ROOT / "prompts" / "themes.txt"
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def load_styles() -> list[str]:
    path = PROJECT_ROOT / "prompts" / "styles.txt"
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def log_run_result(run_id: str, result: dict, config: dict) -> Path:
    logs_dir = PROJECT_ROOT / config["output"]["logs_dir"]
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"run_{timestamp}_{run_id[:8]}.json"
    log_path.write_text(json.dumps(result, indent=2, default=str))
    return log_path


def run_full_pipeline(
    theme: str = None,
    style: str = None,
    image_count: int = None,
    dry_run: bool = False,
    skip_webhooks: bool = False,
    skip_cleanup: bool = False,
) -> dict:
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    config = load_config()

    run_result = {
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "completed_at": None,
        "success": False,
        "dry_run": dry_run,
        "theme": None,
        "style": None,
        "image_count": 0,
        "steps": {},
        "errors": [],
    }

    logger.info(f"{'='*60}")
    logger.info(f"RUN START | run_id={run_id}")
    logger.info(f"{'='*60}")

    # ── Step 1: Select theme and style ───────────────────────────
    try:
        themes = load_themes()
        styles = load_styles()
        theme = theme or random.choice(themes)
        style = style or random.choice(styles)

        count_cfg = config["image_generation"]["images_per_pack"]
        image_count = image_count or random.randint(count_cfg["min"], count_cfg["max"])

        run_result["theme"] = theme
        run_result["style"] = style
        run_result["image_count"] = image_count

        logger.info(f"Selected: theme={theme} | style={style} | count={image_count}")
        run_result["steps"]["select"] = {"success": True}
    except Exception as e:
        run_result["errors"].append(f"select: {e}")
        run_result["steps"]["select"] = {"success": False, "error": str(e)}
        logger.error(f"Failed to select theme/style: {e}")
        return _finalize(run_result, started_at, config)

    # ── Step 2: Generate images ───────────────────────────────────
    try:
        logger.info(f"STEP 2: Generating {image_count} images...")
        from scripts.generate_images import generate_pack

        output_base = PROJECT_ROOT / config["output"]["base_dir"]
        gen_result = generate_pack(
            theme=theme,
            style=style,
            image_count=image_count,
            output_dir=output_base,
            config=config,
            dry_run=dry_run,
        )
        run_result["steps"]["generate_images"] = gen_result

        if gen_result["generated"] == 0:
            raise RuntimeError("No images were generated successfully")

        actual_count = gen_result["generated"]
        run_result["image_count"] = actual_count
        logger.info(f"Generated {actual_count}/{image_count} images")

    except Exception as e:
        run_result["errors"].append(f"generate_images: {e}")
        run_result["steps"]["generate_images"] = {"success": False, "error": str(e)}
        logger.error(f"Image generation failed: {e}\n{traceback.format_exc()}")
        return _finalize(run_result, started_at, config)

    # ── Step 3: Create ZIP ────────────────────────────────────────
    zip_path = None
    try:
        logger.info("STEP 3: Creating ZIP...")
        from scripts.prepare_zip import zip_theme_folder

        theme_dir = output_base / theme
        zips_dir = PROJECT_ROOT / config["output"]["zips_dir"]
        zip_result = zip_theme_folder(theme_dir, zips_dir)
        run_result["steps"]["prepare_zip"] = zip_result

        if zip_result.get("success"):
            zip_path = Path(zip_result["zip_path"])
            logger.info(f"ZIP created: {zip_result['zip_filename']} ({zip_result['zip_size_mb']}MB)")
        else:
            raise RuntimeError(f"ZIP creation failed: {zip_result.get('reason')}")

    except Exception as e:
        run_result["errors"].append(f"prepare_zip: {e}")
        run_result["steps"]["prepare_zip"] = {"success": False, "error": str(e)}
        logger.error(f"ZIP creation failed: {e}")

    # ── Step 4: Generate manifest ─────────────────────────────────
    try:
        logger.info("STEP 4: Generating manifest...")
        from scripts.generate_manifest import generate_manifest

        manifest = generate_manifest(
            theme=theme,
            style=style,
            run_id=run_id,
            zip_path=zip_path,
            config=config,
        )
        run_result["steps"]["generate_manifest"] = {
            "success": True,
            "pack_id": manifest["pack_id"],
            "marketplace_ready": manifest["marketplace_ready"],
        }
        logger.info(f"Manifest generated: pack_id={manifest['pack_id']}")

    except Exception as e:
        run_result["errors"].append(f"generate_manifest: {e}")
        run_result["steps"]["generate_manifest"] = {"success": False, "error": str(e)}
        logger.error(f"Manifest generation failed: {e}")

    # ── Step 5: Send to webhooks ──────────────────────────────────
    if not skip_webhooks and config["automation"]["send_to_zapier"]:
        try:
            logger.info("STEP 5: Sending to Zapier webhooks...")
            from scripts.send_to_webhook import send_all_webhooks

            webhook_results = send_all_webhooks(theme, config, zip_path)
            run_result["steps"]["send_webhooks"] = webhook_results
            sent_count = sum(1 for r in webhook_results if r.get("success") and not r.get("skipped"))
            logger.info(f"Webhooks sent: {sent_count}/{len(webhook_results)}")

        except Exception as e:
            run_result["errors"].append(f"send_webhooks: {e}")
            run_result["steps"]["send_webhooks"] = {"success": False, "error": str(e)}
            logger.error(f"Webhook sending failed: {e}")
    else:
        logger.info("STEP 5: Webhook sending skipped")
        run_result["steps"]["send_webhooks"] = {"skipped": True}

    # ── Step 6: Cleanup ───────────────────────────────────────────
    if not skip_cleanup and config["automation"]["cleanup_after_run"]:
        try:
            logger.info("STEP 6: Cleaning up output...")
            from scripts.cleanup import cleanup_theme

            theme_dir = output_base / theme
            cleanup_result = cleanup_theme(theme_dir, keep_manifest=True)
            run_result["steps"]["cleanup"] = cleanup_result
            logger.info(f"Cleanup: {cleanup_result['removed']} files removed")

        except Exception as e:
            run_result["errors"].append(f"cleanup: {e}")
            run_result["steps"]["cleanup"] = {"success": False, "error": str(e)}
            logger.warning(f"Cleanup failed (non-critical): {e}")
    else:
        logger.info("STEP 6: Cleanup skipped")
        run_result["steps"]["cleanup"] = {"skipped": True}

    return _finalize(run_result, started_at, config)


def _finalize(run_result: dict, started_at: datetime, config: dict) -> dict:
    from datetime import datetime, timezone

    completed_at = datetime.now(timezone.utc)
    run_result["completed_at"] = completed_at.isoformat()
    run_result["duration_seconds"] = round(
        (completed_at - started_at).total_seconds(), 2
    )

    step_successes = [
        s.get("success", s.get("skipped", False))
        for s in run_result["steps"].values()
        if isinstance(s, dict)
    ]
    run_result["success"] = all(step_successes) and not run_result["errors"]

    log_path = log_run_result(run_result["run_id"], run_result, config)

    status = "SUCCESS" if run_result["success"] else "PARTIAL/FAILED"
    logger.info(f"{'='*60}")
    logger.info(f"RUN {status} | run_id={run_result['run_id']}")
    logger.info(f"Duration: {run_result['duration_seconds']}s")
    logger.info(f"Log: {log_path}")
    logger.info(f"{'='*60}")

    return run_result


def main():
    parser = argparse.ArgumentParser(
        description="AI Art Pack Generator — Full Automation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_automation.py                          # Random theme + style
  python scripts/run_automation.py --theme cosmic_nebula    # Specific theme
  python scripts/run_automation.py --theme enchanted_forest --style watercolor --count 50
  python scripts/run_automation.py --dry-run                # Test without API calls
  python scripts/run_automation.py --skip-webhooks          # Generate without sending
        """,
    )
    parser.add_argument("--theme", help="Theme name (default: random from themes.txt)")
    parser.add_argument("--style", help="Art style (default: random from styles.txt)")
    parser.add_argument("--count", type=int, help="Number of images (default: random 40-80)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate placeholder images without calling APIs")
    parser.add_argument("--skip-webhooks", action="store_true",
                        help="Skip sending to Zapier")
    parser.add_argument("--skip-cleanup", action="store_true",
                        help="Keep image files after zipping")
    parser.add_argument("--json", action="store_true",
                        help="Output result as JSON")
    args = parser.parse_args()

    # Load .env if python-dotenv is available
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except ImportError:
        pass

    result = run_full_pipeline(
        theme=args.theme,
        style=args.style,
        image_count=args.count,
        dry_run=args.dry_run,
        skip_webhooks=args.skip_webhooks,
        skip_cleanup=args.skip_cleanup,
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
