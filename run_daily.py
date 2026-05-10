#!/usr/bin/env python3
"""
Daily orchestrator: generates AI art packs, zips them, and sends to Zapier webhook.

Required environment variables (not needed for dry runs):
  IMAGE_API_KEY       - Stability AI (DreamStudio) API key
  IMAGE_API_URL       - Image generation endpoint (defaults to DreamStudio SDXL)
  ZAPIER_WEBHOOK_URL  - Zapier "Catch Hook" webhook URL

Optional:
  DRY_RUN=1           - Skip real API calls; write placeholder PNGs and print
                        what would be sent instead of posting to Zapier.

Usage:
  python3 run_daily.py              # live run
  DRY_RUN=1 python3 run_daily.py   # dry run for testing the full pipeline
"""

import os
import sys
import shutil
import datetime

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")


def clean_output():
    output_dir = os.path.join(REPO_ROOT, "output")
    for item in os.listdir(output_dir):
        if item == ".keep":
            continue
        item_path = os.path.join(output_dir, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)
    print("Output folder cleaned.")


def run():
    label = " [DRY RUN]" if DRY_RUN else ""
    print(f"\n{'='*60}")
    print(f"AI Art Pack Generation{label} — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    from generate_images import generate_images
    from prepare_zip import zip_packs
    from send_to_webhook import send_files

    print("Step 1/4: Generating images...")
    manifest = generate_images(dry_run=DRY_RUN)

    print("\nStep 2/4: Creating zip archives...")
    zip_files = zip_packs()

    print("\nStep 3/4: Sending to Zapier webhook...")
    send_files(zip_files, manifest, dry_run=DRY_RUN)

    print("\nStep 4/4: Cleaning output folder...")
    clean_output()

    print(f"\n{'='*60}")
    print(f"Run complete{label}.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()
