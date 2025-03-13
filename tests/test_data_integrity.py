# tests/test_data_integrity.py

import pytest
import pandas as pd
import re
from typing import List, Dict, Any

########################
# If real data is available:
########################
try:
    from ss_roster2csv.io_utils import read_roster
    from ss_roster2csv.parser import (
        parse_header_keys,
        find_course_pages,
        build_long_table,
    )
    REAL_DATA_AVAILABLE = True
except ImportError:
    # Skip real-data tests if imports fail.
    REAL_DATA_AVAILABLE = False


########################
# Utility: Check missing line numbers
########################
def check_missing_lines(
    df: pd.DataFrame, course_id_col: str = "crsno"
) -> pd.DataFrame:
    """
    Detects missing student line numbers in each course.

    Returns:
        pd.DataFrame containing ['course_id', 'missing_lines'].
    """
    results = []
    grouped = df.groupby(course_id_col)
    for c_id, group in grouped:
        # Convert 'LineNo' to numeric
        group_line_nos = (
            pd.to_numeric(group["LineNo"], errors="coerce").dropna().astype(int)
        )
        if group_line_nos.empty:
            results.append({course_id_col: c_id, "missing_lines": []})
            continue
        max_line = group_line_nos.max()
        existing = set(group_line_nos.unique())
        all_possible = set(range(1, max_line + 1))
        missing = sorted(all_possible - existing)
        if missing:
            results.append({course_id_col: c_id, "missing_lines": missing})
    return pd.DataFrame(results)


########################
# **Invariant: "Total" must be followed by a number**
########################

@pytest.fixture
def mock_pages_for_total() -> List[List[str]]:
    return [
        ["Course", "ACCT 202", "Semester", "2", "StudentID", "Email", "1", "TU-56789", "John Doe", "Total", "37"],
        ["Course", "BFIN 402", "Semester", "1", "StudentID", "Email", "1", "TU-99999", "Jane Roe", "Total", "???"],
        ["Course", "COMP 101", "Semester", "2", "StudentID", "Email", "1", "TU-11111", "Jon Snow"],
    ]


def test_total_followed_by_number(mock_pages_for_total):
    """Ensure 'Total' is always followed by an integer."""
    for idx, page in enumerate(mock_pages_for_total):
        if "Total" in page:
            t_index = page.index("Total")
            assert t_index + 1 < len(page), f"Page {idx}: 'Total' at end; no number follows."
            next_token = page[t_index + 1]
            try:
                int(next_token)
            except ValueError:
                pytest.fail(f"Page {idx}: 'Total' is followed by '{next_token}', which is not a number")


########################
# **Invariant: "Email" must exist**
########################

@pytest.fixture
def mock_pages_for_email() -> List[List[str]]:
    return [
        ["Course", "ACCT 202", "Semester", "2", "StudentID", "Email", "1", "TU-56789", "John Doe"],
        ["Course", "BFIN 402", "Semester", "1", "StudentID", "Full Name", "1", "TU-99999"],
    ]


def test_email_presence(mock_pages_for_email):
    """Each page must contain 'Email'."""
    for idx, page in enumerate(mock_pages_for_email):
        assert "Email" in page, f"Page {idx} missing 'Email': {page}"


########################
# **Invariant: Course headers must contain expected fields**
########################

@pytest.fixture
def mock_course_headers() -> List[Dict[str, Any]]:
    return [
        {"Course": "ACCT 202", "Semester": "2", "Instructor": "John Doe"},
        {"Course": "BFIN 402", "Instructor": "Jane Roe"},
        {"Course": "COMP 101", "Semester": "2"},
    ]


def test_course_headers(mock_course_headers):
    """Ensure each parsed course header contains at least 'Course' and 'Semester'."""
    for idx, header in enumerate(mock_course_headers):
        assert "Course" in header, f"Course header {idx} missing 'Course': {header}"
        assert "Semester" in header, f"Course header {idx} missing 'Semester': {header}"


########################
# **Invariant: Student ID Format**
########################

@pytest.fixture
def mock_student_ids() -> List[str]:
    return [
        "12345", "TU-67890", "99999", "AB123", "TU-XYZ12"
    ]


def test_student_id_format(mock_student_ids):
    """Ensure student IDs match either 'TU-#####' or just '#####'."""
    student_id_pattern = re.compile(r"^(TU-\d{5}|\d{5})$")
    for student_id in mock_student_ids:
        assert student_id_pattern.match(student_id), f"Invalid student ID: {student_id}"


########################
# **Optional: Real Data Checks**
########################

@pytest.mark.skipif(not REAL_DATA_AVAILABLE, reason="Real data not available.")
def test_real_data_invariants():
    """Run full validation on real data."""
    pages = read_roster("roster_250303.txt")
    courses = find_course_pages(pages)
    cr_data = []
    for c in courses:
        header, body = parse_header_keys(c), []
        cr_data.append((header, body))

    # Validate headers
    for i, (header, _) in enumerate(cr_data):
        assert "Course" in header, f"Real-data course {i} missing 'Course'"
        assert "Semester" in header, f"Real-data course {i} missing 'Semester'"

    # Validate 'Email' presence
    for i, page in enumerate(pages):
        assert "Email" in page, f"Real-data: Page {i} missing 'Email'"

    # Validate missing line numbers
    df = build_long_table(cr_data)
    missing_df = check_missing_lines(df)
    assert missing_df.empty, f"Some courses have missing line numbers: {missing_df}"


########################
# **Run with: pytest tests/test_data_integrity.py**
########################

