#!/usr/bin/env python3
"""
Generates SEO-optimized titles, descriptions, and tags for all marketplaces.
Uses Claude API when available, with template fallback.
"""

import os
import sys
import json
import random
import logging
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.config_loader import load_config

logger = setup_logger("generate_seo")

# Theme → human-readable display mapping
THEME_DISPLAY = {
    "cosmic_nebula": "Cosmic Nebula Space",
    "enchanted_forest": "Enchanted Magical Forest",
    "ancient_temple": "Ancient Mystical Temple",
    "underwater_kingdom": "Underwater Ocean Kingdom",
    "neon_city_night": "Neon City Night Life",
    "autumn_harvest": "Autumn Harvest Season",
    "cherry_blossom_japan": "Japanese Cherry Blossom Sakura",
    "desert_dunes": "Desert Sand Dunes",
    "arctic_aurora": "Arctic Aurora Borealis Northern Lights",
    "tropical_paradise": "Tropical Paradise Beach",
    "gothic_cathedral": "Gothic Cathedral Architecture",
    "medieval_market": "Medieval Fantasy Market",
    "space_station": "Space Station Sci-Fi",
    "haunted_mansion": "Haunted Gothic Mansion",
    "fairy_tale_cottage": "Fairy Tale Storybook Cottage",
    "volcano_eruption": "Dramatic Volcano Eruption",
    "bamboo_zen_garden": "Bamboo Japanese Zen Garden",
    "steampunk_workshop": "Steampunk Victorian Workshop",
    "vintage_botanical": "Vintage Botanical Illustration",
    "crystal_cave": "Crystal Cave Gemstone",
    "mountain_sunrise": "Mountain Sunrise Landscape",
    "rainy_street_reflections": "Rainy Street Night Reflections",
    "greek_mythology": "Greek Mythology Gods",
    "egyptian_pharaoh": "Ancient Egyptian Pharaoh",
    "viking_village": "Viking Norse Village",
    "renaissance_portrait": "Renaissance Fine Art Portrait",
    "art_deco_glamour": "Art Deco Glamour Gold",
    "witches_brew": "Halloween Witch Magic Potion",
    "dragon_lair": "Fantasy Dragon Lair Cave",
    "mermaid_cove": "Mermaid Ocean Fantasy Cove",
    "celestial_maps": "Celestial Star Map Astronomy",
    "deep_sea_creatures": "Deep Sea Ocean Creatures",
    "magical_mushroom_forest": "Magical Mushroom Fantasy Forest",
    "cyberpunk_alley": "Cyberpunk Neon Alley Future",
    "samurai_dojo": "Japanese Samurai Warrior Dojo",
    "aztec_ruins": "Ancient Aztec Ruins Jungle",
    "northern_lights": "Northern Lights Aurora Sky",
    "sunflower_fields": "Sunflower Fields Summer Nature",
    "winter_wonderland": "Winter Wonderland Snow Holiday",
    "moonlit_ocean": "Moonlit Ocean Night Sea",
}

USE_CASES = [
    "digital downloads",
    "printable wall art",
    "social media backgrounds",
    "website backgrounds",
    "Canva designs",
    "blog graphics",
    "YouTube thumbnails",
    "presentation backgrounds",
    "desktop wallpapers",
    "phone wallpapers",
    "digital scrapbooking",
    "print-on-demand products",
    "Zoom virtual backgrounds",
    "marketing materials",
    "creative projects",
]

MOODS = [
    "stunning", "breathtaking", "ethereal", "mystical", "vibrant",
    "dramatic", "serene", "enchanting", "mesmerizing", "captivating",
]


def load_seo_keywords(theme: str) -> dict:
    keywords_path = PROJECT_ROOT / "prompts" / "seo_keywords.txt"
    theme_keywords = []
    universal_keywords = []

    if not keywords_path.exists():
        return {"theme": [], "universal": []}

    current_section = None
    for line in keywords_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("##"):
            current_section = line[2:].strip().lower()
            continue
        if line.startswith("#"):
            continue
        if "|" in line:
            key, kws = line.split("|", 1)
            if key.strip() == theme:
                theme_keywords.extend([k.strip() for k in kws.split(",")])
        elif current_section and "universal" in current_section:
            universal_keywords.extend([k.strip() for k in line.split(",")])

    return {"theme": theme_keywords, "universal": universal_keywords}


def generate_etsy_title(theme: str, style: str, image_count: int, config: dict) -> str:
    theme_display = THEME_DISPLAY.get(theme, theme.replace("_", " ").title())
    style_display = style.replace("_", " ").title()
    max_chars = config["seo"]["title_max_chars"]

    title = (
        f"{theme_display} {style_display} Digital Art Pack | "
        f"{image_count} High Resolution Images | Commercial Use | Instant Download"
    )
    return title[:max_chars]


def generate_etsy_description(theme: str, style: str, image_count: int) -> str:
    theme_display = THEME_DISPLAY.get(theme, theme.replace("_", " ").title())
    style_display = style.replace("_", " ")
    mood = random.choice(MOODS)
    use_case_list = random.sample(USE_CASES, 6)
    use_cases_text = "\n".join(f"• {uc.title()}" for uc in use_case_list)

    return f"""✨ {mood.upper()} {theme_display.upper()} DIGITAL ART PACK ✨

Elevate your creative projects with this stunning collection of {image_count} premium {style_display} style digital images featuring {theme_display} themes. Each image is professionally crafted for maximum visual impact and commercial versatility.

📦 WHAT'S INCLUDED:
• {image_count} high-resolution PNG images
• Files sized for print and digital use (1024×1024 to 1792×1024)
• Instant ZIP download — no waiting!
• Full commercial use license included

🎨 PERFECT FOR:
{use_cases_text}

🔑 WHY YOU'LL LOVE IT:
✓ Commercial license — sell products, use in client work
✓ Instant download — files available immediately after purchase
✓ High resolution — crisp and clear at any size
✓ Unique AI art — exclusive designs you won't find elsewhere
✓ Consistent style — cohesive look across all images in the pack

📐 TECHNICAL DETAILS:
• Format: PNG (high quality, transparent background support)
• Resolution: 1024px × 1024px minimum (many at 1792px wide)
• Color mode: sRGB
• DPI: 300 (print ready)

💼 LICENSE TERMS:
✅ Personal projects — YES
✅ Commercial products — YES (POD, digital sales, client work)
✅ Social media — YES
✅ Print products — YES (mugs, shirts, posters, etc.)
❌ Resale of original files — NO
❌ Claiming as your own AI-free artwork — NO

⚡ INSTANT DOWNLOAD:
After purchase, you'll receive a ZIP file containing all {image_count} images. No shipping, no waiting — start creating immediately!

Questions? Message me anytime. I respond within 24 hours.

#digitalart #{theme.replace('_', '')} #{style.replace(' ', '')} #instantdownload #commercialuse"""


def generate_etsy_tags(theme: str, style: str, config: dict) -> list[str]:
    max_tags = config["seo"]["etsy_tags_count"]
    max_chars = config["seo"]["etsy_tag_max_chars"]

    theme_words = theme.replace("_", " ").split()
    style_words = style.replace("_", " ").split()

    base_tags = [
        "digital art",
        "instant download",
        "commercial use",
        "digital download",
        "printable art",
        "wall art print",
        "high resolution",
        style[:max_chars],
        " ".join(theme_words[:2])[:max_chars],
        "digital bundle",
        "art pack",
        "background images",
        "royalty free art",
    ]

    keyword_data = load_seo_keywords(theme)
    theme_kws = keyword_data.get("theme", [])

    all_tags = base_tags.copy()
    for kw in theme_kws:
        if len(kw) <= max_chars and kw not in all_tags:
            all_tags.append(kw)

    seen = set()
    unique_tags = []
    for tag in all_tags:
        tag_clean = tag.strip()[:max_chars]
        if tag_clean and tag_clean not in seen:
            seen.add(tag_clean)
            unique_tags.append(tag_clean)

    return unique_tags[:max_tags]


def generate_creative_market_content(
    theme: str, style: str, image_count: int, config: dict
) -> dict:
    theme_display = THEME_DISPLAY.get(theme, theme.replace("_", " ").title())
    style_display = style.replace("_", " ").title()

    title = f"{image_count} {theme_display} {style_display} Background Images Bundle"

    description = f"""A premium collection of {image_count} {style_display.lower()} {theme_display.lower()} background images for designers, bloggers, and content creators.

All images are high-resolution, commercially licensed, and ready to use in your next project. Perfect for Photoshop, Canva, Figma, and any design software.

INCLUDED IN THIS BUNDLE:
— {image_count} PNG image files
— Multiple aspect ratios (square, landscape, portrait)
— 300 DPI print-ready quality
— Commercial use license
— Instant download

COMPATIBLE WITH:
Adobe Photoshop, Illustrator, InDesign, Canva, Figma, Affinity Designer, Sketch, and any software that supports PNG files.

LICENSE: Commercial use included. Use in unlimited personal and commercial projects."""

    kw_data = load_seo_keywords(theme)
    keywords = [
        f"{style_display.lower()} backgrounds",
        f"{theme_display.lower()} images",
        "digital backgrounds",
        "background bundle",
        "commercial license",
        "high resolution",
        "PNG files",
        "instant download",
        "design assets",
        "creative bundle",
    ]
    keywords.extend(kw_data.get("theme", [])[:5])

    return {
        "title": title[:100],
        "description": description,
        "keywords": keywords[:config["seo"]["creative_market_keywords_count"]],
    }


def generate_adobe_stock_content(
    theme: str, style: str, config: dict
) -> list[dict]:
    theme_display = THEME_DISPLAY.get(theme, theme.replace("_", " ").title())
    style_display = style.replace("_", " ")
    max_title = config["seo"]["adobe_stock_title_max_chars"] if "adobe_stock_title_max_chars" in config["seo"] else 70
    max_kw = config["seo"]["adobe_stock_keywords_count"]

    kw_data = load_seo_keywords(theme)
    base_kws = [
        theme_display.lower(),
        style_display,
        "digital art",
        "background",
        "illustration",
        "AI generated",
        "commercial use",
        "high resolution",
        "abstract",
        "creative",
    ]
    theme_kws = kw_data.get("theme", [])
    universal_kws = kw_data.get("universal", [])[:10]
    all_kws = list(dict.fromkeys(base_kws + theme_kws + universal_kws))[:max_kw]

    entries = []
    moods = ["dramatic", "ethereal", "vibrant", "moody", "serene"]
    for i, mood in enumerate(moods[:3]):
        title = f"{theme_display} {style_display} - {mood} digital background"[:max_title]
        entries.append({
            "title": title,
            "keywords": all_kws,
            "category": "Backgrounds/Textures",
        })

    return entries


def generate_seo_package(
    theme: str, style: str, image_count: int, config: dict
) -> dict:
    logger.info(f"Generating SEO package for theme={theme}, style={style}")

    etsy_title = generate_etsy_title(theme, style, image_count, config)
    etsy_description = generate_etsy_description(theme, style, image_count)
    etsy_tags = generate_etsy_tags(theme, style, config)
    cm_content = generate_creative_market_content(theme, style, image_count, config)
    adobe_entries = generate_adobe_stock_content(theme, style, config)

    price_tiers = config["marketplace"]["price_usd"]
    if image_count <= 15:
        price = price_tiers["small_pack_10_images"]
    elif image_count <= 30:
        price = price_tiers["medium_pack_25_images"]
    elif image_count <= 60:
        price = price_tiers["large_pack_50_images"]
    else:
        price = price_tiers["mega_pack_75_plus"]

    return {
        "etsy": {
            "title": etsy_title,
            "description": etsy_description,
            "tags": etsy_tags,
            "price_usd": price,
            "category": "Art & Collectibles > Prints > Digital Prints",
            "shipping_profile": "digital_download",
        },
        "creative_market": cm_content,
        "adobe_stock": adobe_entries,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate SEO content for a pack")
    parser.add_argument("--theme", required=True)
    parser.add_argument("--style", required=True)
    parser.add_argument("--count", type=int, default=50)
    args = parser.parse_args()

    config = load_config()
    seo = generate_seo_package(args.theme, args.style, args.count, config)
    print(json.dumps(seo, indent=2))
