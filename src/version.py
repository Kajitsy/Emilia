from pathlib import Path

_version_file = Path(__file__).resolve().parent.parent / "VERSION"
if _version_file.exists():
    __version__ = _version_file.read_text(encoding="utf-8").strip()
else:
    __version__ = "3.3.4"

__version_info__ = tuple(
    int(x) if x.isdigit() else x for x in __version__.replace("-", ".").split(".")
)
