# tests/test_parser.py

import pytest
from ss_roster2csv import parser


def test_make_one_empty():
    assert parser.make_one([]) == []


def test_make_one_single():
    c = [["A", "B", "C"]]
    assert parser.make_one(c) == ["A", "B", "C"]


def test_make_one_double():
    c = [["A", "B"], ["C", "D"]]
    assert parser.make_one(c) == ["A", "B", "C", "D"]


# Additional tests for find_course_pages, split_head_body, etc.
