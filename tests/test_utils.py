from core.utils import hex_to_rgba, is_version_at_least, parse_color, rgba_to_hex


def test_is_version_at_least_standard():
    assert is_version_at_least("1.13.2", "1.13.1") is True
    assert is_version_at_least("1.13.1", "1.13.2") is False
    assert is_version_at_least("2.0.0", "1.9.9") is True
    assert is_version_at_least("1.13", "1.13.0") is True  # 1.13 vs 1.13.0
    assert is_version_at_least("1.13.0", "1.13") is True  # 1.13.0 vs 1.13


def test_is_version_at_least_operators():
    # >= operator
    assert is_version_at_least("1.13.2", ">=1.13.1") is True
    assert is_version_at_least("1.13.1", ">=1.13.2") is False

    # <= operator
    assert is_version_at_least("1.13.1", "<=1.13.2") is True
    assert is_version_at_least("1.13.2", "<=1.13.1") is False

    # > operator
    assert is_version_at_least("1.13.2", ">1.13.1") is True
    assert is_version_at_least("1.13.2", ">1.13.2") is False

    # < operator
    assert is_version_at_least("1.13.1", "<1.13.2") is True
    assert is_version_at_least("1.13.1", "<1.13.1") is False

    # == and = operator
    assert is_version_at_least("1.13.2", "==1.13.2") is True
    assert is_version_at_least("1.13.2", "=1.13.2") is True
    assert is_version_at_least("1.13.1", "==1.13.2") is False

    # multiple operators
    assert is_version_at_least("1.13.5", ">=1.13.0, <=1.14.0") is True
    assert is_version_at_least("1.15.0", ">=1.13.0, <=1.14.0") is False
    assert is_version_at_least("1.12.0", ">=1.13.0, <=1.14.0") is False
    assert is_version_at_least("1.13.2", ">1.13.0,<1.14.0") is True


def test_is_version_at_least_rc():
    # Final is greater than rc
    assert is_version_at_least("1.13.2", "1.13.2rc2") is True
    assert is_version_at_least("1.13.2rc2", "1.13.2") is False

    # rc is greater than previous version
    assert is_version_at_least("1.13.2rc2", "1.13.1") is True
    assert is_version_at_least("1.13.1", "1.13.2rc2") is False

    # Compare rcs
    assert is_version_at_least("1.13.2rc3", "1.13.2rc2") is True
    assert is_version_at_least("1.13.2rc2", "1.13.2rc3") is False

    # Same rc
    assert is_version_at_least("1.13.2rc2", "1.13.2rc2") is True


def test_is_version_at_least_invalid():
    assert is_version_at_least("abc", "1.13.1") is False
    assert is_version_at_least("1.13.1", "abc") is False
    assert is_version_at_least("1.13.x", "1.13.1") is False
    assert is_version_at_least(None, "1.13.1") is False
    assert is_version_at_least("1.13.1", None) is False


def test_is_version_at_least_missing_dots():
    assert is_version_at_least("2", "1") is True
    assert is_version_at_least("1", "2") is False


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
