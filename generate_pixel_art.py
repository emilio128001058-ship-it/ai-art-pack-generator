#!/usr/bin/env python3
"""
Generates a pixel art image pack using Stability AI v2beta Core.
Costs ~3 credits per image.

Usage:
    source .env && python3 generate_pixel_art.py           # 10 images
    source .env && python3 generate_pixel_art.py --count 5 # custom count
"""

import os
import sys
import json
import random
import argparse
import datetime
import requests

API_KEY = os.environ.get("IMAGE_API_KEY")
API_URL = os.environ.get(
    "IMAGE_API_URL",
    "https://api.stability.ai/v2beta/stable-image/generate/core",
)

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(REPO_ROOT, "output", "pixel_art")

SUBJECTS = [
    "a knight in armor",
    "a wizard casting a spell",
    "a dragon breathing fire",
    "a medieval village at sunset",
    "a space explorer on an alien planet",
    "a pirate ship on the ocean",
    "a forest with glowing mushrooms",
    "a dungeon with treasure chests",
    "a cat sitting on a rooftop",
    "a warrior princess with a sword",
    "a cozy tavern interior",
    "a desert pyramid at night",
    "an underwater kingdom",
    "a robot in a neon city",
    "a snowy mountain cabin",
    "a witch's potion shop",
    "a cyberpunk street market",
    "a fairy garden with flowers",
]

PIXEL_STYLES = [
    "16-bit pixel art, SNES style",
    "8-bit pixel art, NES style",
    "32-bit pixel art, retro RPG",
    "pixel art, Game Boy color palette",
    "pixel art, isometric view",
    "pixel art, top-down RPG perspective",
    "pixel art, side-scrolling platformer style",
    "pixel art, detailed sprite art",
]


def build_prompt(subject, style):
    return (
        f"{subject}, {style}, vibrant colors, clean pixel art, "
        "no blur, sharp edges, retro game aesthetic, high quality"
    )


def generate(count=10):
    if not API_KEY:
        print("ERROR: IMAGE_API_KEY not set. Run: source .env && python3 generate_pixel_art.py")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    manifest = {
        "pack": "pixel_art",
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "images": [],
    }

    print(f"Generating {count} pixel art image(s) → {OUTPUT_DIR}\n")

    for i in range(1, count + 1):
        subject = random.choice(SUBJECTS)
        style = random.choice(PIXEL_STYLES)
        prompt = build_prompt(subject, style)
        filename = f"pixel_art_{i:02d}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)

        print(f"[{i}/{count}] {subject} | {style}")
        print(f"         Prompt: {prompt[:80]}...")

        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Accept": "image/*"},
            data={"prompt": prompt, "output_format": "png", "aspect_ratio": "1:1"},
            files={"none": ""},
            timeout=60,
        )

        if response.ok:
            with open(filepath, "wb") as f:
                f.write(response.content)
            size_kb = len(response.content) // 1024
            print(f"         Saved {filename} ({size_kb} KB)\n")
            manifest["images"].append({"file": filename, "prompt": prompt, "style": style})
        else:
            print(f"         WARNING: {response.status_code} — {response.text[:100]}\n",
                  file=sys.stderr)

    manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    saved = len(manifest["images"])
    credits_used = saved * 3
    print(f"Done. {saved}/{count} images saved.")
    print(f"Estimated credits used: ~{credits_used}")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate pixel art images")
    parser.add_argument("--count", type=int, default=10, help="Number of images (default: 10)")
    args = parser.parse_args()
    generate(count=args.count)
