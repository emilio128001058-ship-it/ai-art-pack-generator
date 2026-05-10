import os
import requests
import json
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def send_files(zip_files, manifest, dry_run=False):
    if dry_run:
        print("[DRY RUN] Would send these files to Zapier webhook:")
        for z in zip_files:
            print(f"  - {os.path.basename(z)}")
        print("  - manifest.json")
        print("[DRY RUN] Skipping actual HTTP POST.")
        return

    webhook_url = os.environ.get("ZAPIER_WEBHOOK_URL")
    if not webhook_url:
        print("ERROR: ZAPIER_WEBHOOK_URL environment variable must be set", file=sys.stderr)
        sys.exit(1)

    manifest_json = json.dumps(manifest)

    for zip_file in zip_files:
        print(f"Sending {os.path.basename(zip_file)}...")
        with open(zip_file, "rb") as f:
            files = {"file": (os.path.basename(zip_file), f, "application/zip")}
            data = {"manifest": manifest_json}
            try:
                response = requests.post(webhook_url, files=files, data=data, timeout=120)
                if response.ok:
                    print(f"  OK: {os.path.basename(zip_file)}")
                else:
                    print(
                        f"  WARNING: {os.path.basename(zip_file)} returned {response.status_code}",
                        file=sys.stderr,
                    )
            except requests.RequestException as e:
                print(f"  ERROR sending {os.path.basename(zip_file)}: {e}", file=sys.stderr)

    manifest_path = os.path.join(REPO_ROOT, "output", "manifest.json")
    if os.path.exists(manifest_path):
        print("Sending manifest.json...")
        with open(manifest_path, "rb") as f:
            files = {"file": ("manifest.json", f, "application/json")}
            try:
                response = requests.post(webhook_url, files=files, timeout=30)
                print(
                    "  OK: manifest.json"
                    if response.ok
                    else f"  WARNING: manifest.json returned {response.status_code}"
                )
            except requests.RequestException as e:
                print(f"  ERROR sending manifest.json: {e}", file=sys.stderr)


if __name__ == "__main__":
    dry = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
    output_dir = os.path.join(REPO_ROOT, "output")
    manifest_path = os.path.join(output_dir, "manifest.json")

    if not os.path.exists(manifest_path):
        print("ERROR: output/manifest.json not found. Run generate_images.py first.", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    zip_files = [
        os.path.join(output_dir, fname)
        for fname in os.listdir(output_dir)
        if fname.endswith(".zip")
    ]

    if not zip_files:
        print("WARNING: No zip files found. Run prepare_zip.py first.", file=sys.stderr)
        sys.exit(1)

    send_files(zip_files, manifest, dry_run=dry)
