import os
import requests
import json
import random
import struct
import sys
import zlib
import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Stability AI DreamStudio default endpoint
STABILITY_AI_URL = (
    "https://api.stability.ai/v1/generation/"
    "stable-diffusion-xl-1024-v1-0/text-to-image"
)


def load_list(relative_path):
    with open(os.path.join(REPO_ROOT, relative_path), "r") as f:
        return [line.strip() for line in f if line.strip()]


def generate_prompt(theme, style):
    return f"{theme}, in the style of {style}, high resolution, detailed, professional quality"


def _placeholder_png():
    """Create a minimal valid 1×1 PNG for dry-run testing (no external deps)."""
    def chunk(name, data):
        crc = zlib.crc32(name + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", crc)

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xaa\xcc\xff"))  # blue-ish pixel
    iend = chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend


def generate_images(dry_run=False):
    if not dry_run:
        api_key = os.environ.get("IMAGE_API_KEY")
        api_url = os.environ.get("IMAGE_API_URL", STABILITY_AI_URL)

        if not api_key:
            print("ERROR: IMAGE_API_KEY environment variable must be set", file=sys.stderr)
            sys.exit(1)

    styles = load_list("prompts/styles.txt")
    themes = load_list("prompts/themes.txt")

    n_themes = 1 if dry_run else 2
    images_per_theme_range = (2, 3) if dry_run else (20, 40)

    selected_themes = random.sample(themes, min(n_themes, len(themes)))
    manifest = {
        "packs": [],
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "dry_run": dry_run,
    }

    for theme in selected_themes:
        theme_key = theme.replace(" ", "_").replace("/", "_").replace("&", "and")
        theme_folder = os.path.join(REPO_ROOT, "output", theme_key)
        os.makedirs(theme_folder, exist_ok=True)

        pack_info = {"theme": theme, "images": []}
        count = random.randint(*images_per_theme_range)

        for i in range(1, count + 1):
            style = random.choice(styles)
            prompt = generate_prompt(theme, style)
            filename = f"{theme_key}_{style.replace(' ', '_')}_{i}.png"
            filepath = os.path.join(theme_folder, filename)

            if dry_run:
                with open(filepath, "wb") as f:
                    f.write(_placeholder_png())
                print(f"  [DRY RUN] wrote placeholder: {filename}")
            else:
                payload = {
                    "text_prompts": [{"text": prompt, "weight": 1}],
                    "cfg_scale": 7,
                    "height": 1024,
                    "width": 1024,
                    "steps": 30,
                    "samples": 1,
                }
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "image/png",
                    "Content-Type": "application/json",
                }
                try:
                    response = requests.post(
                        api_url, json=payload, headers=headers, timeout=60
                    )
                    response.raise_for_status()
                except requests.RequestException as e:
                    print(f"  WARNING: image {i} for '{theme}' failed: {e}", file=sys.stderr)
                    continue

                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"  saved: {filename}")

            pack_info["images"].append({"file": filename, "prompt": prompt, "style": style})

        manifest["packs"].append(pack_info)

    manifest_path = os.path.join(REPO_ROOT, "output", "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    total = sum(len(p["images"]) for p in manifest["packs"])
    label = "[DRY RUN] " if dry_run else ""
    print(f"{label}Generated {total} images across {len(manifest['packs'])} theme(s)")
    return manifest


if __name__ == "__main__":
    dry = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
    generate_images(dry_run=dry)
