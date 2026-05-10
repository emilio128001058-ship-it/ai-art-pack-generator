import os
import requests
import json
import random
import sys
import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_list(relative_path):
    with open(os.path.join(REPO_ROOT, relative_path), "r") as f:
        return [line.strip() for line in f if line.strip()]


def generate_prompt(theme, style):
    return f"{theme}, in the style of {style}, high resolution, detailed, professional quality"


def generate_images():
    api_key = os.environ.get("IMAGE_API_KEY")
    api_url = os.environ.get("IMAGE_API_URL")

    if not api_key or not api_url:
        print(
            "ERROR: IMAGE_API_KEY and IMAGE_API_URL environment variables must be set",
            file=sys.stderr,
        )
        sys.exit(1)

    styles = load_list("prompts/styles.txt")
    themes = load_list("prompts/themes.txt")

    selected_themes = random.sample(themes, min(2, len(themes)))
    manifest = {
        "packs": [],
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
    }

    for theme in selected_themes:
        theme_key = theme.replace(" ", "_").replace("/", "_").replace("&", "and")
        theme_folder = os.path.join(REPO_ROOT, "output", theme_key)
        os.makedirs(theme_folder, exist_ok=True)

        pack_info = {"theme": theme, "images": []}
        images_per_theme = random.randint(20, 40)

        for i in range(1, images_per_theme + 1):
            style = random.choice(styles)
            prompt = generate_prompt(theme, style)

            payload = {"prompt": prompt}
            headers = {"Authorization": f"Bearer {api_key}"}

            try:
                response = requests.post(api_url, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"WARNING: Failed image {i} for '{theme}': {e}", file=sys.stderr)
                continue

            filename = f"{theme_key}_{style.replace(' ', '_')}_{i}.png"
            filepath = os.path.join(theme_folder, filename)

            with open(filepath, "wb") as f:
                f.write(response.content)

            pack_info["images"].append({"file": filename, "prompt": prompt, "style": style})

        manifest["packs"].append(pack_info)

    manifest_path = os.path.join(REPO_ROOT, "output", "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    total = sum(len(p["images"]) for p in manifest["packs"])
    print(f"Generated {total} images across {len(manifest['packs'])} themes")
    return manifest


if __name__ == "__main__":
    generate_images()
