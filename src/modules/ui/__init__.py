from .AnimatedBackground import (
    AnimatedBackgroundWidget,
    MediaBackgroundWidget,
    VideoBackgroundThread,
    extract_media_palette,
)
from .ThemeManager import ThemeManager

TM = ThemeManager()

__all__ = [
    "TM",
    "ThemeManager",
    "AnimatedBackgroundWidget",
    "MediaBackgroundWidget",
    "VideoBackgroundThread",
    "extract_media_palette",
]

