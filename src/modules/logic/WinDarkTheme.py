"""
Py-Win-Styles
Author: Akash Bora
Version: 1.8
Link: https://github.com/Akascape/py-window-styles
"""

from __future__ import annotations

from typing import Any

try:
    import platform
    import winreg
    from ctypes import (
        POINTER,
        WINFUNCTYPE,
        Structure,
        byref,
        c_buffer,
        c_int,
        c_uint64,
        pointer,
        sizeof,
        windll,
    )
    from ctypes.wintypes import DWORD, ULONG

except ImportError:
    raise ImportError("WinDarkTheme import errror: No windows environment detected!")


def ChangeDWMAttrib(hWnd: int, attrib: int, color) -> None:
    windll.dwmapi.DwmSetWindowAttribute(hWnd, attrib, byref(color), sizeof(c_int))


def detect(window: Any):
    """detect the type of UI library and return HWND"""
    try:  # tkinter
        window.update()
        return windll.user32.GetParent(window.winfo_id())
    except:
        pass
    try:  # pyqt/pyside
        return window.winId().__int__()
    except:
        pass
    try:  # wxpython
        return window.GetHandle()
    except:
        pass
    if isinstance(window, int):
        return window  # other ui windows hwnd
    else:
        return windll.user32.GetActiveWindow()  # get active hwnd
