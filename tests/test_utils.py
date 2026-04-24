import os
import sys
import pytest

# Add the project root to sys.path so Minify can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Minify.core.utils import hex_to_rgba, rgba_to_hex, parse_color


def test_hex_to_rgba():
    # 6-char hex
    assert hex_to_rgba("#ff0000") == [255, 0, 0, 255]
    assert hex_to_rgba("00ff00") == [0, 255, 0, 255]

    # 8-char hex
    assert hex_to_rgba("#0000ff80") == [0, 0, 255, 128]
    assert hex_to_rgba("12345678") == [18, 52, 86, 120]

    # Invalid characters (ValueError fallback)
    assert hex_to_rgba("#ffxx00") == [255, 255, 255, 255]

    # Invalid lengths (IndexError fallback)
    assert hex_to_rgba("#ff000") == [255, 255, 255, 255]  # 5 chars
    assert hex_to_rgba("#ff00000") == [255, 255, 255, 255]  # 7 chars


def test_rgba_to_hex():
    # Standard RGBA list
    assert rgba_to_hex([255, 0, 0, 255]) == "#ff0000ff"
    assert rgba_to_hex([0, 255, 0, 128]) == "#00ff0080"

    # Clamping out-of-bounds values
    assert rgba_to_hex([300, -10, 0, 500]) == "#ff0000ff"

    # Invalid types / lengths (fallback to #ffffffff)
    assert rgba_to_hex([255, 0, 0]) == "#ffffffff"  # Short list
    assert rgba_to_hex(None) == "#ffffffff"  # None
    assert rgba_to_hex("not a list") == "#ffffffff"  # Invalid type


def test_parse_color():
    # List passed directly
    assert parse_color([100, 150, 200, 255]) == [100, 150, 200, 255]

    # Valid string
    assert parse_color("#00ff00") == [0, 255, 0, 255]

    # Invalid or None values (fallback via hex_to_rgba("#ffffffff"))
    assert parse_color(None) == [255, 255, 255, 255]
    assert parse_color(123) == [255, 255, 255, 255]
    assert parse_color("") == [255, 255, 255, 255]
