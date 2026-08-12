import os
import shutil


def clean_build():
    base_dir = os.path.join(os.getcwd(), "dist", "main")

    if not os.path.exists(base_dir):
        return

    targets = [
        {
            "path": os.path.join(base_dir, "_internal", "speech_recognition", "pocketsphinx-data"),
            "type": "dir"
        },
        {
            "path": os.path.join(base_dir, "_internal", "PyQt6", "Qt6", "resources",
                                 "qtwebengine_devtools_resources.debug.pak"),
            "type": "file"
        }
    ]

    for item in targets:
        path = item["path"]
        if os.path.exists(path):
            if item["type"] == "dir":
                shutil.rmtree(path)
            else:
                os.remove(path)


if __name__ == "__main__":
    clean_build()
