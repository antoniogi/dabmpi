import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.file_utils import SMALL_FILE_THRESHOLD, tail


def test_tail_returns_last_line():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8") as tmp:
        tmp.write("first line\nsecond line\nthird line\n")
        tmp_path = tmp.name

    try:
        assert tail(tmp_path) == "third line"
    finally:
        Path(tmp_path).unlink()


def test_tail_empty_file_returns_empty():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8") as tmp:
        tmp_path = tmp.name

    try:
        assert tail(tmp_path) == ""
    finally:
        Path(tmp_path).unlink()


def test_tail_with_no_trailing_newline():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8") as tmp:
        tmp.write("single line without newline")
        tmp_path = tmp.name

    try:
        assert tail(tmp_path) == "single line without newline"
    finally:
        Path(tmp_path).unlink()


def test_tail_large_file_uses_large_path(monkeypatch):
    import core.file_utils as file_utils

    monkeypatch.setattr(file_utils, "SMALL_FILE_THRESHOLD", 1)

    with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as tmp:
        tmp.write(b"line1\nline2\nline3\n")
        tmp_path = tmp.name

    try:
        assert tail(tmp_path) == "line3"
    finally:
        Path(tmp_path).unlink()
