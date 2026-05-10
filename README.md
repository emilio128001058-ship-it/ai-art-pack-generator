# AI Art Pack Generator

A fully automated system that generates AI art packs and publishes them to multiple marketplaces (Etsy, Creative Market, Adobe Stock) for passive income.

## What It Does

Each automated run:
1. Randomly selects a **theme** (cosmic nebula, enchanted forest, etc.) and **art style** (watercolor, cyberpunk, etc.)
2. Generates **40–80 AI images** via OpenAI DALL-E 3 or Stability AI
3. Creates a **ZIP pack** ready for marketplace upload
4. Generates a **manifest.json** with full SEO content for all marketplaces
5. Sends everything to **Zapier** for automatic marketplace distribution
6. **Cleans up** the output directory for the next run
7. **Logs** all results for tracking

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your keys
```

### 3. Run the full pipeline

```bash
# Random theme + style (production run)
python scripts/run_automation.py

# Test run without API calls
python scripts/run_automation.py --dry-run

# Specific theme and style
python scripts/run_automation.py --theme cosmic_nebula --style watercolor --count 50
```

---

## Repository Structure

```
ai-art-pack-generator/
├── scripts/
│   ├── run_automation.py      # Main orchestrator — runs full pipeline
│   ├── generate_images.py     # AI image generation (OpenAI / Stability)
│   ├── generate_manifest.py   # Creates manifest.json with all metadata
│   ├── generate_seo.py        # SEO titles, descriptions, tags per marketplace
│   ├── prepare_zip.py         # Zips theme folders into distributable packs
│   ├── send_to_webhook.py     # POSTs to Zapier with full payload
│   └── cleanup.py             # Clears output after run
├── prompts/
│   ├── themes.txt             # 40 art pack themes (one per line)
│   ├── styles.txt             # 30 art styles (one per line)
│   ├── instructions.txt       # Image generation quality instructions
│   └── seo_keywords.txt       # SEO keywords by marketplace and theme
├── config/
│   ├── settings.json          # Main configuration
│   ├── marketplaces.json      # Per-marketplace listing requirements
│   └── webhooks.json          # Zapier webhook URLs + payload schema
├── utils/
│   ├── logger.py              # Centralized logging
│   └── config_loader.py       # Cached config loading
├── tests/
│   ├── test_image_generation.py
│   ├── test_zip_creation.py
│   └── test_webhook_payload.py
├── output/                    # Generated images (gitignored)
│   └── zips/                  # Packaged ZIPs (gitignored)
├── logs/                      # Run logs (gitignored)
├── .env.example               # API key template
├── requirements.txt
└── CLAUDE.md                  # Instructions for Claude automation
```

---

## Configuration

### settings.json

| Key | Description |
|-----|-------------|
| `image_generation.provider` | `"openai"` or `"stability"` |
| `image_generation.images_per_pack.min/max` | Range for random image count |
| `image_generation.quality` | `"hd"` or `"standard"` |
| `marketplace.price_usd` | Pricing tiers by pack size |
| `automation.cleanup_after_run` | Auto-clean images after zipping |
| `automation.send_to_zapier` | Enable/disable webhook sending |

### Adding a New Theme

```bash
echo "my_new_theme" >> prompts/themes.txt
```

Then add theme-specific SEO keywords to `prompts/seo_keywords.txt`:
```
my_new_theme|keyword one,keyword two,keyword three
```

### Adding a New Style

```bash
echo "impressionist painting" >> prompts/styles.txt
```

---

## Webhook Payload

The system sends a single JSON payload to Zapier containing all marketplace data:

```json
{
  "pack_id": "uuid",
  "theme": "cosmic_nebula",
  "image_count": 50,
  "zip_filename": "cosmic_nebula_20240101.zip",
  "zip_base64": "...(if under 10MB)...",
  "gdrive_path": "AI Art Packs/2024-01/cosmic_nebula",
  "etsy_title": "Cosmic Nebula Watercolor Digital Art Pack | 50 Images...",
  "etsy_tags": ["digital art", "space art", "..."],
  "etsy_price_usd": 14.99,
  "creative_market_title": "50 Cosmic Nebula Watercolor Backgrounds Bundle",
  "creative_market_keywords": ["cosmic", "nebula", "..."],
  "adobe_stock_title": "Cosmic nebula watercolor - ethereal digital background",
  "adobe_stock_keywords": ["cosmic", "nebula", "space", "..."]
}
```

---

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_webhook_payload.py -v

# Run with coverage
python -m pytest tests/ --cov=scripts --cov=utils
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key for DALL-E 3 |
| `STABILITY_API_KEY` | Yes* | Stability AI API key (fallback) |
| `ANTHROPIC_API_KEY` | No | Claude API for enhanced SEO |
| `ZAPIER_MAIN_WEBHOOK_URL` | No | Main Zapier distribution webhook |
| `ZAPIER_ETSY_WEBHOOK_URL` | No | Etsy-specific Zapier webhook |
| `ZAPIER_GDRIVE_WEBHOOK_URL` | No | Google Drive upload webhook |

*At least one image generation API key is required for production runs.

---

## Scheduling Daily Runs

### Using cron

```bash
crontab -e
# Add:
0 7 * * * cd /path/to/ai-art-pack-generator && source .env && python scripts/run_automation.py
```

### Using GitHub Actions

See `CLAUDE.md` for a complete GitHub Actions workflow configuration.

---

## API Cost Estimates

| Provider | Cost per image | 50 images | Daily (monthly) |
|----------|---------------|-----------|-----------------|
| OpenAI DALL-E 3 HD | $0.080 | $4.00 | ~$120/month |
| OpenAI DALL-E 3 Standard | $0.040 | $2.00 | ~$60/month |
| Stability AI SDXL | ~$0.002 | $0.10 | ~$3/month |

**Revenue potential:** $9.99–$14.99/pack on Etsy × 30 packs/month = ~$300–$450 gross/month.

---

## License

This automation system is for personal use. Generated art is commercially licensable per your AI provider's terms. Review OpenAI's usage policies before selling.
