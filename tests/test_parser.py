# tests/test_parser.py

import pytest
import logging
from ss_roster2csv import parser
from ss_roster2csv.mytypes import Course, Courses, HeaderInfo, BodyInfo

logger = logging.getLogger(__name__)


# ------------------------
# Test: make_one
# ------------------------
def test_make_one_empty():
    """Ensure merging an empty list results in an empty output."""
    assert parser.make_one([]) == []


def test_make_one_single():
    """Ensure merging a single page remains unchanged."""
    c = [["A", "B", "C"]]
    assert parser.make_one(c) == ["A", "B", "C"]


def test_make_one_double():
    """Ensure merging two pages results in a concatenated list."""
    c = [["A", "B"], ["C", "D"]]
    assert parser.make_one(c) == ["A", "B", "C", "D"]


# ------------------------
# Test: find_course_pages
# ------------------------
@pytest.fixture
def mock_pages():
    """Fixture providing mock pages with and without 'Total'."""
    return [
        ["Course", "ACCT 102", "Semester", "2", "StudentID", "Email", "1", "TU-12345", "John Doe", "Total"],
        ["Course", "BFIN 402", "Semester", "1", "StudentID", "Email", "1", "TU-67890", "Jane Smith"],
    ]


def test_find_course_pages(mock_pages):
    """Ensure pages are correctly split into courses."""
    result = parser.find_course_pages(mock_pages)
    assert isinstance(result, list)
    assert len(result) == 2  # Expecting two courses


# ------------------------
# Test: split_head_body
# ------------------------
@pytest.fixture
def mock_course():
    """Fixture providing a mock course split into header and body."""
    return ["Course", "ACCT 102", "Semester", "2", "StudentID", "Full Name", "Email", "1", "TU-12345", "John Doe", "Total"]


def test_split_head_body(mock_course):
    """Ensure header and body are correctly separated."""
    header, body = parser.split_head_body(mock_course)
    assert isinstance(header, list) and isinstance(body, list)
    assert "StudentID" in header
    assert "Email" in header
    assert "1" in body  # Student data


# ------------------------
# Test: get_courses_info
# ------------------------
@pytest.fixture
def mock_courses():
    """Fixture providing mock courses with students."""
    return [
        ["Course", "ACCT 102", "Semester", "2", "StudentID", "Full Name", "Email", "1", "TU-12345", "John Doe", "Total"],
        ["Course", "BFIN 402", "Semester", "1", "StudentID", "Full Name", "Email", "1", "TU-67890", "Jane Smith", "Total"],
    ]


def test_get_courses_info(mock_courses):
    """Ensure course info extraction works correctly."""
    courses_info = parser.get_courses_info(mock_courses)
    assert len(courses_info) == 2
    assert isinstance(courses_info[0], tuple)
    assert isinstance(courses_info[0][0], list)  # Header
    assert isinstance(courses_info[0][1], list)  # Students


# ------------------------
# Test: get_students
# ------------------------
@pytest.fixture
def mock_students():
    """Fixture providing mock student data."""
    return ["1", "TU-12345", "John Doe", "2", "TU-67890", "Jane Smith"]


def test_get_students(mock_students):
    """Ensure multiple students are extracted correctly."""
    students = parser.get_students(mock_students)
    assert len(students) == 2
    assert students[0] == ("1", "TU-12345", "John Doe")


# ------------------------
# Test: get_lonely_students
# ------------------------
@pytest.fixture
def mock_single_student():
    """Fixture providing a single student entry."""
    return ["TU-98765", "Solo Student"]


def test_get_lonely_students(mock_single_student):
    """Ensure a single student case is handled correctly."""
    students = parser.get_lonely_students(mock_single_student)
    assert len(students) == 1
    assert students[0] == (1, "TU-98765", "Solo Student")


# ------------------------
# Test: build_long_table
# ------------------------
@pytest.fixture
def mock_crs_data():
    """Fixture providing mock course data for DataFrame testing."""
    return [
        (["Course", "ACCT 102", "Semester", "2"], [("1", "TU-12345", "John Doe")]),
        (["Course", "BFIN 402", "Semester", "1"], [("2", "TU-67890", "Jane Smith")]),
    ]


def test_build_long_table(mock_crs_data):
    """Ensure course data is converted into a DataFrame."""
    df = parser.build_long_table(mock_crs_data)
    assert not df.empty
    assert len(df) == 2
    assert set(df.columns) >= {"LineNo", "StudentID", "FullName", "Course", "Semester"}


# ------------------------
# Test: parse_header_keys
# ------------------------
@pytest.fixture
def mock_header():
    """Fixture providing a sample course header."""
    return ["Course", "ACCT 102", "Semester", "2", "Instructor", "Dr. Smith"]


def test_parse_header_keys(mock_header):
    """Ensure headers are correctly parsed into a dictionary."""
    result = parser.parse_header_keys(mock_header)
    assert isinstance(result, dict)
    assert result["Course"] == "ACCT 102"
    assert result["Semester"] == "2"
    assert result["Instructor"] == "Dr. Smith"


# ------------------------
# Test: is_number
# ------------------------
@pytest.mark.parametrize(
    "value, expected",
    [
        ("42", 42),
        ("3.14", None),  # Since `is_number` only checks integers
        ("abc", None),
    ],
)
def test_is_number(value, expected):
    """Ensure number parsing works correctly."""
    assert parser.is_number(value) == expected



# Additional tests for find_course_pages, split_head_body, etc.
