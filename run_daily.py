#!/usr/bin/env python3
"""
Daily orchestrator: generates AI art packs, zips them, and sends to Zapier webhook.

Required environment variables:
  IMAGE_API_KEY       - API key for the image generation service
  IMAGE_API_URL       - Endpoint URL for the image generation service
  ZAPIER_WEBHOOK_URL  - Zapier catch webhook URL

Optional: create a .env file at the repo root and run_daily.sh will source it automatically.
"""

import os
import sys
import shutil
import datetime

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))


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
    print(f"\n{'='*60}")
    print(f"AI Art Pack Generation — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    from generate_images import generate_images
    from prepare_zip import zip_packs
    from send_to_webhook import send_files

    print("Step 1/4: Generating images...")
    manifest = generate_images()

    print("\nStep 2/4: Creating zip archives...")
    zip_files = zip_packs()

    print("\nStep 3/4: Sending to Zapier webhook...")
    send_files(zip_files, manifest)

    print("\nStep 4/4: Cleaning output folder...")
    clean_output()

    print(f"\n{'='*60}")
    print("Run complete.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()
