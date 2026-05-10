import os
import zipfile

def zip_packs():
    output_dir = "output"
    zips = []

    for folder in os.listdir(output_dir):
        folder_path = os.path.join(output_dir, folder)

        if os.path.isdir(folder_path) and folder != "__pycache__":
            zip_name = f"{folder}.zip"
            zip_path = os.path.join(output_dir, zip_name)

            with zipfile.ZipFile(zip_path, "w") as zipf:
                for file in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file)
                    zipf.write(file_path, arcname=file)

            zips.append(zip_path)

    return zips
