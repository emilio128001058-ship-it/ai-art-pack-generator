import requests

WEBHOOK_URL = "YOUR_ZAPIER_WEBHOOK_URL"

def send_files(zip_files, manifest):
    for zip_file in zip_files:
        with open(zip_file, "rb") as f:
            files = {"file": (zip_file, f, "application/zip")}
            data = {"manifest": manifest}
            requests.post(WEBHOOK_URL, files=files, data=data)
