import sys
from pathlib import Path
import pytest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from Utils import tail


def test_tail_empty_file(tmp_path):
    f = tmp_path / "empty.txt"

    f.write_text("")

    assert tail(str(f)) == ""


def test_tail_single_line_no_newline(tmp_path):
    f = tmp_path / "single.txt"

    f.write_text("hello")

    assert tail(str(f)) == "hello"


def test_tail_single_line_with_newline(tmp_path):
    f = tmp_path / "single_newline.txt"

    f.write_text("hello\n")

    assert tail(str(f)) == "hello"


def test_tail_multiple_lines(tmp_path):
    f = tmp_path / "multi.txt"

    f.write_text(
        "line1\n"
        "line2\n"
        "line3\n"
    )

    assert tail(str(f)) == "line3"


def test_tail_no_trailing_newline(tmp_path):
    f = tmp_path / "no_newline.txt"

    f.write_text(
        "line1\n"
        "line2"
    )

    assert tail(str(f)) == "line2"


def test_tail_unicode(tmp_path):
    f = tmp_path / "unicode.txt"

    f.write_text(
        "hello\n"
        "κόσμος\n",
        encoding="utf-8"
    )

    assert tail(str(f)) == "κόσμος"


def test_tail_large_file_path(tmp_path, monkeypatch):
    import Utils

    monkeypatch.setattr(
        Utils,
        "SMALL_FILE_THRESHOLD",
        1,
    )

    f = tmp_path / "large.txt"

    lines = [f"line{i}" for i in range(1000)]

    f.write_text("\n".join(lines))

    assert tail(str(f)) == "line999"


def test_tail_missing_file():
    with pytest.raises(FileNotFoundError):
        tail("/this/file/does/not/exist.txt")