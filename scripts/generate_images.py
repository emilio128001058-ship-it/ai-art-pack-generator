#!/usr/bin/env python3
"""
Reads prompt themes and styles, generates 40-80 images per theme via AI APIs,
and saves them to output/<theme>/.
"""

import os
import sys
import json
import time
import random
import base64
import logging
import argparse
import requests
from pathlib import Path
from typing import Optional

# Allow running from project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.config_loader import load_config

logger = setup_logger("generate_images")


def load_themes(themes_path: Path) -> list[str]:
    return [
        line.strip()
        for line in themes_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def load_styles(styles_path: Path) -> list[str]:
    return [
        line.strip()
        for line in styles_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def load_instructions(instructions_path: Path) -> str:
    return instructions_path.read_text()


def build_prompt(theme: str, style: str, index: int, instructions: str) -> str:
    theme_display = theme.replace("_", " ").title()
    style_display = style.replace("_", " ")

    variations = [
        f"wide establishing shot of {theme_display}",
        f"close-up detail of {theme_display}",
        f"atmospheric scene of {theme_display}",
        f"abstract interpretation of {theme_display}",
        f"moody portrait perspective of {theme_display}",
        f"overhead bird's eye view of {theme_display}",
        f"dramatic low angle of {theme_display}",
        f"symmetrical composition of {theme_display}",
    ]

    variation = variations[index % len(variations)]
    quality_tags = "highly detailed, 8k, masterpiece, award-winning"

    return (
        f"{variation}, {style_display} style, {quality_tags}, "
        f"professional digital art, commercially viable, no text, no watermarks"
    )


def generate_image_openai(
    prompt: str,
    api_key: str,
    size: str = "1024x1024",
    quality: str = "hd",
    style: str = "vivid",
) -> Optional[bytes]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": quality,
        "style": style,
        "response_format": "b64_json",
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        image_b64 = data["data"][0]["b64_json"]
        return base64.b64decode(image_b64)
    except requests.exceptions.HTTPError as e:
        logger.error(f"OpenAI API HTTP error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


def generate_image_stability(
    prompt: str,
    api_key: str,
    width: int = 1024,
    height: int = 1024,
) -> Optional[bytes]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "text_prompts": [
            {"text": prompt, "weight": 1.0},
            {"text": "watermark, text, logo, blurry, low quality, nsfw", "weight": -1.0},
        ],
        "cfg_scale": 7,
        "width": width,
        "height": height,
        "samples": 1,
        "steps": 30,
    }

    try:
        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers=headers,
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        image_b64 = data["artifacts"][0]["base64"]
        return base64.b64decode(image_b64)
    except Exception as e:
        logger.error(f"Stability AI error: {e}")
        return None


def save_image(image_bytes: bytes, output_path: Path) -> bool:
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(image_bytes)
        logger.debug(f"Saved image: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save image {output_path}: {e}")
        return False


def generate_pack(
    theme: str,
    style: str,
    image_count: int,
    output_dir: Path,
    config: dict,
    dry_run: bool = False,
) -> dict:
    theme_dir = output_dir / theme
    theme_dir.mkdir(parents=True, exist_ok=True)

    instructions_path = PROJECT_ROOT / "prompts" / "instructions.txt"
    instructions = load_instructions(instructions_path) if instructions_path.exists() else ""

    provider = config["image_generation"]["provider"]
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    stability_key = os.environ.get("STABILITY_API_KEY", "")

    if not openai_key and not stability_key and not dry_run:
        raise EnvironmentError(
            "No API keys found. Set OPENAI_API_KEY or STABILITY_API_KEY in your .env file."
        )

    batch_size = config["image_generation"].get("batch_size", 5)
    batch_delay = config["image_generation"].get("delay_between_batches_seconds", 2)
    retry_attempts = config["image_generation"].get("retry_attempts", 3)
    retry_delay = config["image_generation"].get("retry_delay_seconds", 5)

    sizes = config["image_generation"].get("image_sizes_varied", ["1024x1024"])
    quality = config["image_generation"].get("quality", "hd")
    img_style = config["image_generation"].get("style", "vivid")

    results = {"theme": theme, "style": style, "generated": 0, "failed": 0, "images": []}
    logger.info(f"Generating {image_count} images | theme={theme} | style={style} | dir={theme_dir}")

    for i in range(image_count):
        filename = f"{theme}_{style.replace(' ', '_')}_{i+1:03d}.png"
        output_path = theme_dir / filename

        if output_path.exists():
            logger.info(f"Skipping existing: {filename}")
            results["generated"] += 1
            results["images"].append(str(output_path))
            continue

        if dry_run:
            logger.info(f"[DRY RUN] Would generate: {filename}")
            output_path.write_bytes(b"PLACEHOLDER")
            results["generated"] += 1
            results["images"].append(str(output_path))
            continue

        prompt = build_prompt(theme, style, i, instructions)
        size = sizes[i % len(sizes)]
        image_bytes = None

        for attempt in range(retry_attempts):
            if attempt > 0:
                logger.info(f"Retry {attempt}/{retry_attempts} for image {i+1}")
                time.sleep(retry_delay * attempt)

            if provider == "openai" and openai_key:
                image_bytes = generate_image_openai(prompt, openai_key, size, quality, img_style)
            elif provider == "stability" or (not openai_key and stability_key):
                w, h = map(int, size.split("x"))
                image_bytes = generate_image_stability(prompt, stability_key, w, h)

            if image_bytes:
                break

            if not image_bytes and openai_key and stability_key:
                logger.warning(f"Primary provider failed, trying fallback for image {i+1}")
                w, h = map(int, size.split("x"))
                image_bytes = generate_image_stability(prompt, stability_key, w, h)
                if image_bytes:
                    break

        if image_bytes and save_image(image_bytes, output_path):
            results["generated"] += 1
            results["images"].append(str(output_path))
            logger.info(f"Generated {i+1}/{image_count}: {filename}")
        else:
            results["failed"] += 1
            logger.error(f"Failed to generate image {i+1}/{image_count}: {filename}")

        if (i + 1) % batch_size == 0 and i < image_count - 1:
            logger.debug(f"Batch complete, waiting {batch_delay}s...")
            time.sleep(batch_delay)

    logger.info(
        f"Pack complete: {results['generated']} generated, {results['failed']} failed"
    )
    return results


def main():
    parser = argparse.ArgumentParser(description="Generate AI art pack images")
    parser.add_argument("--theme", help="Specific theme to generate (default: random)")
    parser.add_argument("--style", help="Specific style to use (default: random)")
    parser.add_argument("--count", type=int, help="Number of images (default: from config)")
    parser.add_argument("--dry-run", action="store_true", help="Run without calling APIs")
    parser.add_argument("--output-dir", help="Override output directory")
    args = parser.parse_args()

    config = load_config()
    img_config = config["image_generation"]
    output_base = Path(args.output_dir or PROJECT_ROOT / config["output"]["base_dir"])

    themes_path = PROJECT_ROOT / "prompts" / "themes.txt"
    styles_path = PROJECT_ROOT / "prompts" / "styles.txt"

    themes = load_themes(themes_path)
    styles = load_styles(styles_path)

    theme = args.theme or random.choice(themes)
    style = args.style or random.choice(styles)

    count_range = img_config["images_per_pack"]
    image_count = args.count or random.randint(count_range["min"], count_range["max"])

    logger.info(f"Starting generation: theme={theme}, style={style}, count={image_count}")

    results = generate_pack(
        theme=theme,
        style=style,
        image_count=image_count,
        output_dir=output_base,
        config=config,
        dry_run=args.dry_run,
    )

    summary_path = output_base / theme / "generation_summary.json"
    summary_path.write_text(json.dumps(results, indent=2))
    logger.info(f"Summary saved to {summary_path}")

    print(json.dumps(results, indent=2))
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
