import os
import json
import hashlib

DIST_FOLDER = "./dist/main"
MANIFEST_FILE = "manifest.json"


def get_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_manifest():
    manifest = {"files": {}}

    for root, _, files in os.walk(DIST_FOLDER):
        for filename in files:
            if filename == MANIFEST_FILE:
                continue

            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, DIST_FOLDER).replace("\\", "/")

            manifest["files"][rel_path] = get_hash(full_path)

    output_path = os.path.join(f"{DIST_FOLDER}", MANIFEST_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)


if __name__ == "__main__":
    create_manifest()