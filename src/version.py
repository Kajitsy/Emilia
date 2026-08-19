import sys
from pathlib import Path


def _load_version() -> str:
    possible_paths = []

    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            possible_paths.append(Path(sys._MEIPASS) / "VERSION")
        exe_dir = Path(sys.executable).resolve().parent
        possible_paths.append(exe_dir / "VERSION")
        possible_paths.append(exe_dir / "_internal" / "VERSION")

    file_dir = Path(__file__).resolve().parent
    possible_paths.append(file_dir.parent / "VERSION")
    possible_paths.append(file_dir / "VERSION")

    for path in possible_paths:
        try:
            if path.exists():
                content = path.read_text(encoding="utf-8").strip()
                if content:
                    return content
        except Exception:
            pass

    return "3.3.6"


__version__ = _load_version()

__version_info__ = tuple(
    int(x) if x.isdigit() else x for x in __version__.replace("-", ".").split(".")
)

