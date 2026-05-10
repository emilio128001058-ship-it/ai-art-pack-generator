# Claude Routine Instructions

1. Run generate_images.py to create themed image packs.
2. Run prepare_zip.py to zip each pack.
3. Run send_to_webhook.py to upload the packs to Zapier.
4. Zapier will:
   - Create Etsy listings
   - Upload to Adobe Stock
   - Upload to Creative Market
5. Repeat this routine daily.

Ensure all images follow the naming format:
theme_style_number.png

Ensure manifest.json is updated every run.
