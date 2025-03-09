# tests/test_io_utils.py

import pytest
from ss_roster2csv import io_utils


def test_read_roster_empty(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")
    pages = io_utils.read_roster(str(empty_file))
    assert pages == []


def test_read_roster_simple(tmp_path):
    f = tmp_path / "simple.txt"
    f.write_text("Line 1\nLine 2\n\x0cLine 3\nSmart School???\n")
    pages = io_utils.read_roster(str(f))
    assert len(pages) == 2
    assert pages[0] == ["Line 1", "Line 2"]
    assert pages[1] == ["Line 3"]
