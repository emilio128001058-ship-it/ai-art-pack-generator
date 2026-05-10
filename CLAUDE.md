# CLAUDE.md — AI Art Pack Generator

This file instructs Claude on how to operate, maintain, and expand this automated AI art pack generation system.

---

## System Overview

This repo generates AI art packs and distributes them to multiple marketplaces for passive income.

**Pipeline (in order):**
1. `generate_images.py` → creates 40–80 images per theme
2. `prepare_zip.py` → packages images into a ZIP
3. `generate_manifest.py` → creates `manifest.json` with SEO + metadata
4. `send_to_webhook.py` → posts to Zapier for marketplace distribution
5. `cleanup.py` → removes images, keeps ZIPs and manifests

**Entry point:** `scripts/run_automation.py`

---

## How Claude Should Run the Scripts

### Full automated run (production)

```bash
python scripts/run_automation.py
```

This selects a random theme + style, runs all 5 pipeline steps, and logs the result.

### Test without API calls

```bash
python scripts/run_automation.py --dry-run
```

Creates placeholder images to test the full pipeline without spending API credits.

### Generate a specific pack

```bash
python scripts/run_automation.py --theme cosmic_nebula --style watercolor --count 50
```

### Run individual steps

```bash
# Step 1: Generate images only
python scripts/generate_images.py --theme enchanted_forest --style "oil painting"

# Step 2: Zip a specific theme
python scripts/prepare_zip.py --theme enchanted_forest

# Step 3: Generate manifest
python scripts/generate_manifest.py --theme enchanted_forest --style "oil painting"

# Step 4: Send to webhooks
python scripts/send_to_webhook.py --theme enchanted_forest

# Step 5: Clean up
python scripts/cleanup.py --theme enchanted_forest
```

### Run the test suite

```bash
python -m pytest tests/ -v
```

---

## How to Generate New Packs

### Standard workflow

1. Ensure `.env` has valid API keys
2. Run: `python scripts/run_automation.py`
3. Check `logs/` for the run result JSON
4. Check `output/zips/` for the packaged ZIP
5. Verify Zapier received the webhook (check Zapier history)

### Adding a new theme

```bash
# Add to themes list
echo "celestial_clockwork" >> prompts/themes.txt

# Add SEO keywords for it
# In prompts/seo_keywords.txt, add a line like:
# celestial_clockwork|steampunk clock,celestial gears,vintage astronomy,clockwork art
```

Then update the `THEME_DISPLAY` dict in `scripts/generate_seo.py`:
```python
"celestial_clockwork": "Celestial Clockwork Steampunk",
```

### Adding a new style

```bash
echo "gouache illustration" >> prompts/styles.txt
```

No other changes needed — styles are used directly in prompts.

### Changing image count

Edit `config/settings.json`:
```json
"images_per_pack": {
    "min": 60,
    "max": 80,
    "default": 70
}
```

Or pass `--count 60` at runtime.

---

## How to Schedule Routines

### Option A: Claude Routines (via cron)

Add to crontab (`crontab -e`):

```bash
# Run daily at 7:00 AM
0 7 * * * cd /path/to/ai-art-pack-generator && source .env && python scripts/run_automation.py >> logs/cron.log 2>&1

# Run twice daily (7 AM and 7 PM) for 2 packs/day
0 7,19 * * * cd /path/to/ai-art-pack-generator && source .env && python scripts/run_automation.py >> logs/cron.log 2>&1

# Weekdays only
0 8 * * 1-5 cd /path/to/ai-art-pack-generator && source .env && python scripts/run_automation.py >> logs/cron.log 2>&1
```

### Option B: GitHub Actions (cloud scheduling)

Create `.github/workflows/daily_run.yml`:

```yaml
name: Daily Art Pack Generation
on:
  schedule:
    - cron: '0 7 * * *'
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/run_automation.py
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ZAPIER_MAIN_WEBHOOK_URL: ${{ secrets.ZAPIER_MAIN_WEBHOOK_URL }}
```

### Option C: Claude Code with /loop skill

If using Claude Code interactively:
```
/loop 24h python scripts/run_automation.py --dry-run
```

---

## How to Handle Errors

### Error: No API keys found

```
EnvironmentError: No API keys found. Set OPENAI_API_KEY or STABILITY_API_KEY in your .env file.
```

**Fix:** Copy `.env.example` to `.env` and add your keys. Verify with:
```bash
grep OPENAI .env
```

### Error: No images were generated successfully

**Causes and fixes:**
1. API rate limit → wait 1 minute, then retry with `--count 10`
2. Invalid API key → check key validity in OpenAI dashboard
3. Content policy violation → review `prompts/themes.txt` for problematic themes
4. Network timeout → check connectivity, retry

### Error: Theme directory not found (manifest step)

```
FileNotFoundError: Theme directory not found: output/cosmic_nebula
```

**Fix:** Images weren't generated. Run Step 1 first:
```bash
python scripts/generate_images.py --theme cosmic_nebula --style watercolor
```

### Error: Webhook sending failed

```
max_retries_exceeded
```

**Diagnosis steps:**
1. Check if webhook URL is set in `.env`
2. Verify webhook is active in Zapier dashboard
3. Check `config/webhooks.json` — is `"active": true`?
4. Test the URL manually:
```bash
curl -X POST YOUR_WEBHOOK_URL -H "Content-Type: application/json" -d '{"test": true}'
```

### Error: ZIP too large

The system warns when ZIP exceeds 10MB for base64 encoding. The ZIP still gets created — it's sent by path/Google Drive, not base64. No action needed.

### Recovering from a partial run

Check the run log in `logs/`:
```bash
ls -lt logs/run_*.json | head -5
cat logs/run_TIMESTAMP_RUNID.json
```

Find which step failed (`"success": false`), then re-run that step manually.

---

## How to Expand the System

### Add a new marketplace

1. Add marketplace config to `config/marketplaces.json`
2. Add SEO generation function to `scripts/generate_seo.py`
3. Include new fields in `build_webhook_payload()` in `scripts/send_to_webhook.py`
4. Add a Zapier webhook entry to `config/webhooks.json`
5. Create the Zap in Zapier

### Add Claude-powered SEO generation

Replace template-based SEO with Claude API calls in `generate_seo.py`:

```python
import anthropic

def generate_etsy_description_with_claude(theme: str, style: str, count: int) -> str:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"Write an Etsy listing description for a {count}-image {theme} art pack in {style} style. Include emojis, bullet points, and a call to action. 200-400 words."
        }]
    )
    return message.content[0].text
```

### Add image upscaling

After generation, add an upscaling step using Real-ESRGAN or similar:
```bash
pip install realesrgan
```

Add `scripts/upscale_images.py` and call it after `generate_images.py` in `run_automation.py`.

### Add watermarked previews

Create `scripts/create_previews.py` that:
1. Takes the first 5 images from each pack
2. Adds a subtle watermark using Pillow
3. Saves to `output/<theme>/previews/`
4. Includes preview URLs in the webhook payload

### Add Shopify integration

1. Use the Shopify MCP tools to create products
2. Add `"shopify"` to `config/marketplaces.json`
3. In Zapier: Webhook → Shopify (create digital product)

### Track revenue with Notion

Create a Zapier Zap: Webhook → Notion (database entry) with fields:
- Pack name, theme, style, image count
- Date generated
- Marketplace listing URLs (fill in after publishing)
- Revenue tracking (update manually or via Etsy API)

---

## Zapier Connection Checklist

### Pre-requisites
- [ ] Zapier account (free tier works for testing; Pro for multi-step Zaps)
- [ ] Marketplace accounts created and verified
- [ ] `.env` file configured with your webhook URLs

### Zap 1: Main Distribution Pipeline

**Trigger:** Webhook by Zapier (Catch Hook)
1. Create Zap → Trigger: "Webhooks by Zapier" → "Catch Hook"
2. Copy the webhook URL → paste into `.env` as `ZAPIER_MAIN_WEBHOOK_URL`
3. Set `"active": true` in `config/webhooks.json` for `main_webhook`
4. Run `python scripts/run_automation.py --dry-run` to test trigger
5. Add Actions:
   - Google Drive: Upload file (use `zip_base64` or path)
   - Email by Zapier: Send notification
   - Notion: Create database item

### Zap 2: Etsy Draft Listing

**Trigger:** Webhook → **Action:** Etsy (Create Listing)
1. Create Zap → Trigger: Webhook catch hook
2. Copy URL → `.env` → `ZAPIER_ETSY_WEBHOOK_URL`
3. Add Action: Etsy → "Create Listing"
4. Map fields:
   - Title → `etsy_title`
   - Description → `etsy_description`
   - Tags → `etsy_tags_string` (comma-separated)
   - Price → `etsy_price_usd`
   - Is Digital → Yes
   - Digital File → upload separately after ZIP arrives on Drive
5. Set `"active": true` in `config/webhooks.json` for `etsy_webhook`

### Zap 3: Google Drive Upload

**Trigger:** Webhook → **Action:** Google Drive (Upload File)
1. Create Zap → Trigger: Webhook
2. Action: Google Drive → "Upload File"
3. Map: File name → `zip_filename`, Folder → `gdrive_path`
4. For file content: use `zip_base64` (if small pack) or set up a download step

### Zap 4: Notion Logging

**Trigger:** Webhook → **Action:** Notion (Create Database Item)
1. Create Notion database with columns: Pack ID, Theme, Style, Images, Date, Status
2. Zap: Webhook → Notion → "Create Database Item"
3. Map fields from payload

### Testing webhooks without Zapier

Use webhook.site for initial testing:
1. Go to webhook.site, copy your unique URL
2. Temporarily set it as `ZAPIER_MAIN_WEBHOOK_URL` in `.env`
3. Run `python scripts/run_automation.py --dry-run`
4. Inspect the full payload at webhook.site

---

## Etsy Connection Checklist

- [ ] Create Etsy seller account at etsy.com/sell
- [ ] Complete identity verification
- [ ] Set up payment account (Etsy Payments)
- [ ] Create shop with banner, logo, about section
- [ ] Set up a "Digital Download" shipping profile (free, instant delivery)
- [ ] Connect Etsy to Zapier (OAuth in Zapier)
- [ ] Create first listing manually to understand the format
- [ ] Enable Zap 2 (Etsy Draft Listing)
- [ ] Test: Run dry-run → verify draft listing appears in Etsy
- [ ] Review and publish first automated draft

**Etsy SEO Tips:**
- Use all 13 tags — the system generates exactly 13
- Front-load the most important keyword in the title
- Use "instant download" and "commercial use" — high buyer search terms
- Price point: $9.99–$14.99 sweet spot for 50-image packs

---

## Creative Market Connection Checklist

- [ ] Apply for a seller account at creativemarket.com/sell
- [ ] Wait for approval (1-3 business days)
- [ ] Complete seller profile and payout setup
- [ ] Learn upload format: ZIP file + preview images + metadata
- [ ] Note: Creative Market does NOT have a public API — upload manually or via Zapier automation
- [ ] Create first product manually to understand requirements
- [ ] Set up Zapier: Webhook → Email notification with all CM metadata
- [ ] Review `creative_market_title`, `creative_market_description`, `creative_market_keywords` in payload

**Creative Market Tips:**
- Preview images matter most — create 8 compelling previews
- Price at $19–$29 for 50-image packs (higher margin than Etsy)
- "Extended license" option available — worth enabling

---

## Adobe Stock Connection Checklist

- [ ] Create Adobe Stock Contributor account at contributor.stock.adobe.com
- [ ] Accept contributor agreement
- [ ] Verify your account
- [ ] Understand AI-generated content policy: must disclose AI generation
- [ ] Note: Adobe Stock requires individual file submission (not ZIPs)
- [ ] Set up workflow: unzip → upload individual PNGs with metadata
- [ ] Add `adobe_stock_keywords_string` and `adobe_stock_title` to each file's metadata
- [ ] Submit 10-image test batch first
- [ ] Wait for review (3-7 days for first batch)
- [ ] After approval, scale up submissions

**Adobe Stock Tips:**
- Keywords are the most important ranking factor
- Use all 50 allowed keywords — the system generates exactly 50
- Title max 70 characters — keep it descriptive, not promotional
- AI disclosure is mandatory — the payload includes `ai_disclosure` field
- Rejection common for first batch — review feedback and resubmit

---

## Monitoring & Maintenance

### Check recent run logs

```bash
ls -lt logs/run_*.json | head -10
cat $(ls -t logs/run_*.json | head -1) | python -m json.tool
```

### Check what's in the output directory

```bash
ls -la output/
ls -la output/zips/
```

### Manual cleanup (if automation fails mid-run)

```bash
python scripts/cleanup.py --keep-manifest
```

### Rotate log files

```bash
python scripts/cleanup.py --clean-logs
```

### Verify test suite passes before deploying changes

```bash
python -m pytest tests/ -v --tb=short
```

---

## API Cost Estimates

| Provider | Cost per image | 50 images | 50 images/day (monthly) |
|----------|---------------|-----------|------------------------|
| OpenAI DALL-E 3 (HD) | $0.080 | $4.00 | ~$120/month |
| OpenAI DALL-E 3 (Standard) | $0.040 | $2.00 | ~$60/month |
| Stability AI (SDXL) | ~$0.002 | $0.10 | ~$3/month |

**Revenue potential:** At $9.99/pack on Etsy × 30 packs/month = $299.70 gross (before Etsy fees ~8%). Break-even with OpenAI HD in under 2 months.

**Recommendation:** Use Stability AI for volume, OpenAI HD for featured/premium packs.
