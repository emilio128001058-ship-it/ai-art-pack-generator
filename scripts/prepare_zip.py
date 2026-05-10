import os
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def zip_packs():
    output_dir = os.path.join(REPO_ROOT, "output")
    zips = []

    for folder_name in os.listdir(output_dir):
        folder_path = os.path.join(output_dir, folder_name)

        if not os.path.isdir(folder_path) or folder_name.startswith("__"):
            continue

        zip_path = os.path.join(output_dir, f"{folder_name}.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    zipf.write(file_path, arcname=filename)

        print(f"Created {zip_path}")
        zips.append(zip_path)

    return zips


if __name__ == "__main__":
    zips = zip_packs()
    print(f"Created {len(zips)} zip file(s)")
