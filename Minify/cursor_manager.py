import ctypes
import dearpygui.dearpygui as ui
from enum import Enum, auto

user32 = ctypes.windll.user32

OCR_NORMAL = 32512  # Target
OCR_SIZENWSE = 32642  # Diagonal left-up <-> right-down
OCR_SIZENESW = 32643  # Diagonal right-up <-> left-down
OCR_SIZEWE = 32644  # Horizontal resize
OCR_SIZENS = 32645  # Vertical resize
OCR_SIZEALL = 32646  # Move
OCR_NO = 32648  # Negative
OCR_HAND = 32649  # Positive
OCR_APPSTARTING = 32650  # Working
SPI_SETCURSORS = 0x0057  # Reset all

user32.LoadCursorW.restype = ctypes.c_void_p  # HCURSOR is a handle (void*)
user32.LoadCursorW.argtypes = [ctypes.c_void_p, ctypes.c_int]  # HINSTANCE, LPCWSTR or int for ID

user32.SetSystemCursor.restype = ctypes.c_bool
user32.SetSystemCursor.argtypes = [ctypes.c_void_p, ctypes.c_uint32]  # HCURSOR, DWORD

user32.SystemParametersInfoW.restype = ctypes.c_bool
user32.SystemParametersInfoW.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]


class cursor_status(Enum):
    DEFAULT = auto()
    SIZENWSE = auto()
    SIZENESW = auto()
    SIZEWE = auto()
    SIZENS = auto()
    SIZEALL = auto()
    NO = auto()
    HAND = auto()
    APPSTARTING = auto()


SIZENWSE = """
cursor = cursor_manager.user32.LoadCursorW(None, cursor_manager.OCR_SIZENWSE)
if not cursor:
    raise RuntimeError("Failed to load cursor")
set_cursor = cursor_manager.user32.SetSystemCursor(cursor, cursor_manager.OCR_NORMAL)
if not set_cursor:
    raise RuntimeError("Failed to set system cursor")
"""

SIZENESW = """
cursor = cursor_manager.user32.LoadCursorW(None, cursor_manager.OCR_SIZENESW)
if not cursor:
    raise RuntimeError("Failed to load cursor")
set_cursor = cursor_manager.user32.SetSystemCursor(cursor, cursor_manager.OCR_NORMAL)
if not set_cursor:
    raise RuntimeError("Failed to set system cursor")
"""

SIZEWE = """
cursor = cursor_manager.user32.LoadCursorW(None, cursor_manager.OCR_SIZEWE)
if not cursor:
    raise RuntimeError("Failed to load cursor")
set_cursor = cursor_manager.user32.SetSystemCursor(cursor, cursor_manager.OCR_NORMAL)
if not set_cursor:
    raise RuntimeError("Failed to set system cursor")
"""

SIZENS = """
cursor = cursor_manager.user32.LoadCursorW(None, cursor_manager.OCR_SIZENS)
if not cursor:
    raise RuntimeError("Failed to load cursor")
set_cursor = cursor_manager.user32.SetSystemCursor(cursor, cursor_manager.OCR_NORMAL)
if not set_cursor:
    raise RuntimeError("Failed to set system cursor")
"""

SIZEALL = """
cursor = cursor_manager.user32.LoadCursorW(None, cursor_manager.OCR_SIZEALL)
if not cursor:
    raise RuntimeError("Failed to load cursor")
set_cursor = cursor_manager.user32.SetSystemCursor(cursor, cursor_manager.OCR_NORMAL)
if not set_cursor:
    raise RuntimeError("Failed to set system cursor")
"""

NO = """
cursor = cursor_manager.user32.LoadCursorW(None, cursor_manager.OCR_NO)
if not cursor:
    raise RuntimeError("Failed to load cursor")
set_cursor = cursor_manager.user32.SetSystemCursor(cursor, cursor_manager.OCR_NORMAL)
if not set_cursor:
    raise RuntimeError("Failed to set system cursor")
"""

HAND = """
cursor = cursor_manager.user32.LoadCursorW(None, cursor_manager.OCR_HAND)
if not cursor:
    raise RuntimeError("Failed to load cursor")
set_cursor = cursor_manager.user32.SetSystemCursor(cursor, cursor_manager.OCR_NORMAL)
if not set_cursor:
    raise RuntimeError("Failed to set system cursor")
"""

APPSTARTING = """
cursor = cursor_manager.user32.LoadCursorW(None, cursor_manager.OCR_APPSTARTING)
if not cursor:
    raise RuntimeError("Failed to load cursor")
set_cursor = cursor_manager.user32.SetSystemCursor(cursor, cursor_manager.OCR_NORMAL)
if not set_cursor:
    raise RuntimeError("Failed to set system cursor")
"""

DEFAULT = """
# Restore all original system cursors
success = cursor_manager.user32.SystemParametersInfoW(cursor_manager.SPI_SETCURSORS, 0, None, 0)
if not success:
    raise RuntimeError("Failed to restore system cursors")
"""
