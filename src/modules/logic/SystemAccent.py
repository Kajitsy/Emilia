import configparser
import os
import platform
import re
import subprocess
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


def get_system_accent_color() -> str:
    """
    Detects the system accent color on Windows and Linux.
    Returns a hex string like '#308cc6'.
    """
    sys_name = platform.system()

    if sys_name == "Windows":
        try:
            import winreg

            # 1. Try DWM AccentColor
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM"
                )
                val, _ = winreg.QueryValueEx(key, "AccentColor")
                winreg.CloseKey(key)
                # Format: 0xAABBGGRR
                r = val & 0xFF
                g = (val >> 8) & 0xFF
                b = (val >> 16) & 0xFF
                return f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                pass

            # 2. Try Explorer AccentColorMenu
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent",
                )
                val, _ = winreg.QueryValueEx(key, "AccentColorMenu")
                winreg.CloseKey(key)
                r = val & 0xFF
                g = (val >> 8) & 0xFF
                b = (val >> 16) & 0xFF
                return f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                pass

            # 3. Try DWM ColorizationColor
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\DWM"
                )
                val, _ = winreg.QueryValueEx(key, "ColorizationColor")
                winreg.CloseKey(key)
                # Format: 0xAARRGGBB
                r = (val >> 16) & 0xFF
                g = (val >> 8) & 0xFF
                b = val & 0xFF
                return f"#{r:02x}{g:02x}{b:02x}"
            except Exception:
                pass
        except Exception:
            pass

    elif sys_name == "Linux":
        # 1. Try XDG Desktop Portal (standard across GNOME, KDE, Hyprland, etc.)
        try:
            res = subprocess.run(
                [
                    "gdbus",
                    "call",
                    "--session",
                    "--dest",
                    "org.freedesktop.portal.Desktop",
                    "--object-path",
                    "/org/freedesktop/portal/desktop",
                    "--method",
                    "org.freedesktop.portal.Settings.Read",
                    "org.freedesktop.appearance",
                    "accent-color",
                ],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if res.returncode == 0 and "(" in res.stdout:
                nums = re.findall(r"([0-9]+\.?[0-9]*)", res.stdout)
                if len(nums) >= 3:
                    r = int(float(nums[0]) * 255)
                    g = int(float(nums[1]) * 255)
                    b = int(float(nums[2]) * 255)
                    if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                        return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            pass

        # 2. Try KDE Plasma kdeglobals
        try:
            kde_path = os.path.expanduser("~/.config/kdeglobals")
            if os.path.exists(kde_path):
                cfg = configparser.ConfigParser()
                cfg.read(kde_path)
                if cfg.has_section("General") and cfg.has_option(
                    "General", "AccentColor"
                ):
                    rgb_str = cfg.get("General", "AccentColor")
                    parts = [
                        int(p.strip())
                        for p in rgb_str.split(",")
                        if p.strip().isdigit()
                    ]
                    if len(parts) == 3:
                        return f"#{parts[0]:02x}{parts[1]:02x}{parts[2]:02x}"
                if cfg.has_section("Colors:Selection") and cfg.has_option(
                    "Colors:Selection", "BackgroundNormal"
                ):
                    rgb_str = cfg.get("Colors:Selection", "BackgroundNormal")
                    parts = [
                        int(p.strip())
                        for p in rgb_str.split(",")
                        if p.strip().isdigit()
                    ]
                    if len(parts) == 3:
                        return f"#{parts[0]:02x}{parts[1]:02x}{parts[2]:02x}"
        except Exception:
            pass

        # 3. Try GNOME / GTK settings
        try:
            res = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "accent-color"],
                capture_output=True,
                text=True,
                timeout=1,
            )
            if res.returncode == 0:
                name = res.stdout.strip().strip("'\"")
                gnome_map = {
                    "blue": "#3584e4",
                    "teal": "#2190a4",
                    "green": "#3a944a",
                    "yellow": "#e5a50a",
                    "orange": "#e66100",
                    "red": "#e01b24",
                    "pink": "#d56199",
                    "purple": "#9141ac",
                    "slate": "#63626c",
                }
                if name in gnome_map:
                    return gnome_map[name]
        except Exception:
            pass

    # 4. Fallback to Qt Application Palette
    app = QApplication.instance()
    if app:
        pal = app.palette()
        c = pal.color(QPalette.ColorRole.Highlight)
        if c.isValid() and c.name() not in ("#000000", "#ffffff"):
            return c.name()

    return "#308cc6"


def adjust_color_brightness(hex_color: str, factor: float) -> str:
    """
    Adjusts the brightness of a hex color by a given factor (>1 for lighter, <1 for darker).
    """
    col = QColor(hex_color)
    if not col.isValid():
        return hex_color

    h, s, v, a = col.getHsvF()
    new_v = max(0.0, min(1.0, v * factor))
    new_col = QColor.fromHsvF(h, s, new_v, a)
    return new_col.name()


def get_contrasting_text_color(hex_color: str) -> str:
    """
    Returns '#ffffff' or '#000000' based on the perceived luminance of the color.
    """
    col = QColor(hex_color)
    if not col.isValid():
        return "#ffffff"
    lum = 0.299 * col.red() + 0.587 * col.green() + 0.114 * col.blue()
    return "#000000" if lum > 150 else "#ffffff"
