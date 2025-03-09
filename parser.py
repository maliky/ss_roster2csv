"""
ss_roster2csv/parser.py

Contains the main functional parsing logic: 
 - Splitting pages into 'courses'
 - Extracting (header, student) data 
 - Building the DataFrame 
 - Minimal changes to your original logic, except logging replaces print.
"""

import logging
import pandas as pd
from typing import List, Tuple, Dict, Any
import re

from .mytypes import (
    CrsHeader,
    Student,
    Students,    
    Page,
    Pages,
    Course,
    Courses,
    StudentData,
    CrsData,
    HeaderInfo,
    BodyInfo,
    CourseInfo,
    CoursesInfo,
)


logger = logging.getLogger(__name__)
COURSE_HEADER_KEYS = [
    "Course",
    "Semester",
    "Course Title",
    "Instructor",
    "Section",
    "Day/Time:",
]
STUD_HEADER = ["StudentID", "Full Name", "Cell #", "Email"]


def find_course_pages(pages: Pages) -> Courses:
    """
    Combine pages into 'courses' by merging them until we see 'Total' in a page.

    Logic:
      1) Accumulate pages into a temporary 'course' list.
      2) If a page contains 'Total' (or is empty after trimming the header), finalize that course.
      3) Move on to the next course block.

    Additionally, if this is not the first page of a course, we remove all lines
    up to 'Email' so that only student data remains.

    Args:
        pages (List[List[str]]): Each page is a list of lines (strings).

    Returns:
        List[List[str]]: A list of merged 'course' blocks, each block a single flat list.
    """
    courses: Courses = []
    course: Course = []

    for idx, page in enumerate(pages):
        empty_page = False

        # If this is not the first page for the current course, strip up to 'Email'.
        if course:
            if "Email" not in page:
                # this should not happened because I've checked that all pages avec Email
                logger.warning(
                    "Page %d does not contain 'Email'; page content might be malformed: %s",
                    idx,
                    page,
                )
            else:
                sidx = page.index("Email")
                page = page[sidx + 1 :]
                empty_page = len(page) == 0

        course.append(page)

        # If we detect 'Total' or the page is empty, we finalize the course block.
        if ("Total" in page) or empty_page:
            courses.append(course)
            course = []

    # Merge each multi-page block into a single list of strings.
    return [make_one(c) for c in courses]


def make_one(course: Courses) -> Course:
    """
    Merge multiple sub-lists (pages) into one single list of strings.
    If there's more than one sub-list, we pairwise concat them
    so that the final result is a single flat list.
     Args:
        course (List[List[str]]): A list of page-blocks, each itself a list of strings.
     Returns:
        List[str]: A flattened single list of strings for the entire course block.
    """
    assert len(course) in [0, 1, 2], f"{len(course)}"
    if len(course) == 2:
        # merges consecutive sub-lists
        result = course[0] + course[1]
    elif len(course) == 1:
        result = course[0]
    elif len(course) == 0:
        result = []

    return result


def get_courses_info(courses: Courses) -> CoursesInfo:
    """
    Parse each 'course' block into a (header, students) structure.

    Steps:
      1) We look for 'StudentID' and 'Email' to find the boundary
         between header tokens and student tokens.
      2) If the student body is very small (<5 tokens), we treat it as a single student
         via `get_lonely_students`.
      3) Otherwise, we parse multiple students via `get_students`.

    Returns:
        A list of (header_tokens, student_chunks), one per course block.
    """
    result: CoursesInfo = []

    for i, course in enumerate(courses):
        if "Email" not in course:
            logger.warning("Course %d has no 'Email' token, skipping body parse.", i)
            result.append((course, []))
            continue

        header, body = split_head_body(course)

        if len(body) < 5:
            students = get_lonely_students(body)
        else:
            students = get_students(body)

        result.append((header, students))
    return result


def split_head_body(course: Course) -> Tuple[HeaderInfo, BodyInfo]:
    """
    Split a flattened course block into (header, body) parts,
    by locating 'StudentID' and 'Email' tokens.

    If 'Total' is missing, we read until the end of the course block for the student region.

    Args:
        course (List[str]): The flat list of tokens for this course.

    Returns:
        (header_tokens, body_tokens)
    """
    if "StudentID" not in course:
        logger.warning("'StudentID' not found in course tokens: %s", course)
        return (course, [])

    head_eidx = course.index("StudentID")

    if "Email" not in course:
        logger.warning("'Email' not found after 'StudentID' in course tokens: %s", course)
        return (course[:head_eidx], [])

    stud_sidx = course.index("Email")
    try:
        stud_eidx = course.index("Total")
    except ValueError:
        stud_eidx = len(course)

    header_tokens = course[:head_eidx]
    body_tokens = course[stud_sidx + 1 : stud_eidx]
    return (header_tokens, body_tokens)


def get_lonely_students(body: BodyInfo) -> Students:
    """
    Handle the special case where there's only one student
    (with no line number or partial data).

    We attempt to match a single TUID + Name with a simple regex.
    """
    if not body:
        return []

    # this course is for one student only and it the line number should be missing
    assert len(body) < 5, f"body={body}"
    student = " ".join(body)
    tuid = r"((?:TU-)?(?<!\d)\d{5})"
    name = r"([^\d+]+)"
    student_pat = f"\\s*{tuid}\\s+{name}"
    stud_match = re.match(student_pat, student)
    if not stud_match:
        logger.warning("Failed to parse single-student body: %s", student)
        return []

    stud = stud_match.groups()
    return [tuple([1] + list(stud))]


def get_students(body: BodyInfo) -> Students:
    """
    Parse multiple student entries from 'body' tokens.
    We assume each student is: (lineNo, TUID, FullName).

    There's no direct phone/email capturing in this minimal approach.
    If phone/emails are present, we skip them for safety.
    """
    student_list = " ".join(body)
    tuid = r"((?:TU-)?(?<!\d)\d{5})"
    name = r"([^\d+]+)"
    rid = (
        r"((?<!\d)\d{1,2})"  # don't need it anymore some student do not have line numbers
    )
    student_pat = f"\\s*{rid}\\s+{tuid}\\s+{name}"

    students: Students = []
    i = 1
    last_lineno = 1

    for stud_match in re.finditer(student_pat, student_list):
        lineno, tu_id, stud_name = stud_match.groups()

        if students:
            cur_lineno = is_number(lineno)
            if last_lineno != 1 and cur_lineno != last_lineno + 1:
                logger.warning(
                    "Non-consecutive line number found: current=%d, previous=%d, tokens=%s",
                    cur_lineno,
                    last_lineno,
                    stud_match,
                )
            last_lineno = cur_lineno
        else:
            last_lineno = 1
        students.append((lineno, tu_id, stud_name))

    return students


def build_long_table(crs: CrsData) -> pd.DataFrame:
    """
    Convert the (header_tokens, student_chunks) into a DataFrame.
    Each row is one student, merging any relevant header keys.

    We only fill 'LineNo', 'StudentID', and 'FullName'.
    The header keys are gleaned from parse_header_keys.
    """
    rows = []
    for i, (header_tokens, student_chunks) in enumerate(crs):
        hdr_dict = parse_header_keys(header_tokens)
        hdr_dict["crsid"] = i

        for chunk in student_chunks:
            if len(chunk) != 3:
                logger.warning(
                    "Unexpected chunk size: %r (expected [lineNo, ID, FullName])", chunk
                )
                continue

            row = dict(hdr_dict)
            row["LineNo"] = chunk[0]
            row["StudentID"] = chunk[1]
            row["FullName"] = chunk[2]
            rows.append(row)

    return pd.DataFrame(rows)


def parse_header_keys(tokens: HeaderInfo) -> CrsHeader:
    """
    Extract key->value pairs from the header portion.
    If a known key is found (in COURSE_HEADER_KEYS) but no valid value follows,
    an empty string is stored. We also skip tokens in STUD_HEADER.
    """
    result: Dict[str, str] = {}
    used_keys = set()
    i = 0
    while i < len(tokens):
        elt = tokens[i]
        # Stop if we see a student header token
        if elt in STUD_HEADER:
            break

        if elt in COURSE_HEADER_KEYS and elt not in used_keys:
            used_keys.add(elt)

            if i + 1 < len(tokens):
                nxt = tokens[i + 1]
                if nxt not in COURSE_HEADER_KEYS and nxt not in STUD_HEADER:
                    result[elt] = nxt.strip(": ")
                    i += 2
                    continue
            # Otherwise store empty
            result[elt] = ""
        i += 1

    return result


def is_number(elt: str) -> Any:
    """
    Try converting 'elt' to an integer or float.
    Return None if not parseable.
    """
    try:
        return int(elt)
    except ValueError:
        pass
    try:
        return float(elt)
    except ValueError:
        return None
