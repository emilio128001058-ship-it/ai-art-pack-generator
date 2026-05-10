import os
import requests
import json
import random

API_KEY = "YOUR_IMAGE_API_KEY"
API_URL = "YOUR_IMAGE_API_ENDPOINT"

def load_list(path):
    with open(path, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def generate_prompt(theme, style):
    return f"{theme}, in the style of {style}, high resolution, detailed, professional quality"

def generate_images():
    styles = load_list("prompts/styles.txt")
    themes = load_list("prompts/themes.txt")

    selected_themes = random.sample(themes, 2)

    manifest = {"packs": []}

    for theme in selected_themes:
        theme_folder = f"output/{theme.replace(' ', '_')}"
        os.makedirs(theme_folder, exist_ok=True)

        pack_info = {"theme": theme, "images": []}

        for i in range(1, 41):
            style = random.choice(styles)
            prompt = generate_prompt(theme, style)

            payload = {"prompt": prompt}
            headers = {"Authorization": f"Bearer {API_KEY}"}

            response = requests.post(API_URL, json=payload, headers=headers)

            filename = f"{theme.replace(' ', '_')}_{style.replace(' ', '_')}_{i}.png"
            filepath = f"{theme_folder}/{filename}"

            with open(filepath, "wb") as f:
                f.write(response.content)

            pack_info["images"].append({
                "file": filename,
                "prompt": prompt,
                "style": style
            })

        manifest["packs"].append(pack_info)

    with open("output/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest
