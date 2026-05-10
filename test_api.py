#!/usr/bin/env python3
"""
Quick single-image test — costs ~3 Stability AI credits.
Run from the repo root after sourcing your .env:

    source .env && python3 test_api.py

Saves the image as test_output.png in the repo root.
"""

import os
import sys
import requests

API_KEY = os.environ.get("IMAGE_API_KEY")
API_URL = os.environ.get(
    "IMAGE_API_URL",
    "https://api.stability.ai/v2beta/stable-image/generate/core",
)
OUTPUT = "test_output.png"

if not API_KEY:
    print("ERROR: IMAGE_API_KEY not set. Run: source .env && python3 test_api.py")
    sys.exit(1)

prompt = "A vibrant sunset over the ocean, cinematic lighting, high resolution, professional quality"
print(f"Prompt : {prompt}")
print(f"API URL: {API_URL}")
print("Generating... (this takes ~5–10 seconds)")

response = requests.post(
    API_URL,
    headers={"Authorization": f"Bearer {API_KEY}", "Accept": "image/*"},
    data={"prompt": prompt, "output_format": "png", "aspect_ratio": "1:1"},
    files={"none": ""},
    timeout=60,
)

if response.ok:
    with open(OUTPUT, "wb") as f:
        f.write(response.content)
    size_kb = len(response.content) // 1024
    print(f"\nSaved {OUTPUT} ({size_kb} KB)")
    print("Test passed.")
else:
    print(f"\nERROR {response.status_code}: {response.text}", file=sys.stderr)
    sys.exit(1)
