import os
import sys

# Add scripts directory to path to import symdump
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from symdump import get_slug


def test_get_slug_basic():
    seen_slugs = set()
    assert get_slug("Hello World", seen_slugs) == "hello-world"
    assert "hello-world" in seen_slugs


def test_get_slug_punctuation():
    seen_slugs = set()
    assert get_slug("Hello, World!", seen_slugs) == "hello-world"
    assert get_slug("Python 3.13", seen_slugs) == "python-313"
    assert get_slug("Test_Under_Score", seen_slugs) == "test_under_score"
    assert get_slug("Test-Hyphen", seen_slugs) == "test-hyphen"


def test_get_slug_spaces():
    seen_slugs = set()
    assert get_slug("  multiple   spaces  ", seen_slugs) == "multiple-spaces"


def test_get_slug_empty_fallback():
    seen_slugs = set()
    assert get_slug("!!!", seen_slugs) == "section"
    assert get_slug("", seen_slugs) == "section-1"


def test_get_slug_uniqueness():
    seen_slugs = set()
    assert get_slug("Header", seen_slugs) == "header"
    assert get_slug("Header", seen_slugs) == "header-1"
    assert get_slug("Header", seen_slugs) == "header-2"


def test_get_slug_complex():
    seen_slugs = set()
    assert get_slug("What is (this)?", seen_slugs) == "what-is-this"
    assert get_slug("What is (this)?", seen_slugs) == "what-is-this-1"
