"""
ss_roster2csv/parser.py

Contains the main functional parsing logic:
 - Splitting pages into 'courses'
 - Extracting (header, student) data
 - Building the DataFrame
"""

import logging
import pandas as pd
import re
from typing import List, Tuple, Dict, Any
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
    "Day/Time",
]
STUD_HEADER = ["StudentID", "Full Name", "Cell #", "Email"]


def find_course_pages(pages: Pages) -> Courses:
    """
    Merge pages into 'courses' by accumulating pages until 'Total' is found.

    Args:
        pages (Pages): A list of pages (each page is a list of text lines).

    Returns:
        Courses: A list of parsed course records.
    """
    courses: Courses = []
    course: Course = []

    for idx, page in enumerate(pages):
        empty_page = False

        if course:
            if "Email" not in page:
                logger.warning(f"Page {idx} lacks 'Email', possible corruption: {page}")
            else:
                sidx = page.index("Email")
                page = page[sidx + 1 :]
                empty_page = len(page) == 0

        course.append(page)

        if "Total" in page or empty_page:
            courses.append(course)
            logger.info(f"Processed course {len(courses)} with {len(course)} pages.")
            course = []

    return [make_one(c) for c in courses]


def make_one(course: Courses) -> Course:
    """
    Merge multiple pages into a single course representation.

    Args:
        course (Courses): List of pages for a single course.

    Returns:
        Course: A single merged list of lines.
    """
    assert len(course) in [0, 1, 2], f"Unexpected page count: {len(course)}"
    return (
        course[0] + course[1]
        if len(course) == 2
        else course[0] if len(course) == 1 else []
    )


def get_courses_info(courses: Courses) -> CoursesInfo:
    """
    Extracts header and student information from courses.

    Args:
        courses (Courses): A list of parsed course pages.

    Returns:
        CoursesInfo: A list of (header, student records) tuples.
    """
    result: CoursesInfo = []

    for i, course in enumerate(courses):
        if "Email" not in course:
            logger.warning(f"Course {i} missing 'Email', skipping student extraction.")
            result.append((course, []))
            continue

        header, body = split_head_body(course)
        hdr_dict = parse_header_keys(header)
        students = get_lonely_students(body) if len(body) < 5 else get_students(body)
        result.append((hdr_dict, students))
        logger.info(
            f"Parsed course {i, hdr_dict['Course']}: {len(students)} students extracted."
        )

    return result


def split_head_body(course: Course) -> Tuple[HeaderInfo, BodyInfo]:
    """
    Splits a course block into header and body parts.

    Args:
        course (Course): Flattened course representation.

    Returns:
        Tuple[HeaderInfo, BodyInfo]: Header and student body data.
    """
    if "StudentID" not in course:
        logger.warning(f"Missing 'StudentID' in course: {course}")
        return course, []

    head_eidx = course.index("StudentID")

    if "Email" not in course:
        logger.warning(f"Missing 'Email' after 'StudentID' in course: {course}")
        return course[:head_eidx], []

    stud_sidx = course.index("Email")

    try:
        stud_eidx = course.index("Total")
    except ValueError:
        stud_eidx = len(course)

    return course[:head_eidx], course[stud_sidx + 1 : stud_eidx]


def get_lonely_students(body: BodyInfo) -> Students:
    """
    Handles cases where only one student is listed.

    Args:
        body (BodyInfo): The student record as a single block.

    Returns:
        Students: A single student record or an empty list.
    """
    if not body:
        return []

    assert len(body) < 5, f"Expected <=4 tokens, found: {body}"
    student_text = " ".join(body)
    tuid = r"((?:TU-)?(?<!\d)\d{5})"
    name = r"([^\d+]+)"
    student_pat = f"\\s*{tuid}\\s+{name}"

    match = re.match(student_pat, student_text)
    if not match:
        logger.warning(f"Could not extract lonely student: {student_text}")
        return []

    return [tuple([1] + list(match.groups()))]


def get_students(body: BodyInfo) -> Students:
    """
    Extracts multiple students from the given body text.

    Args:
        body (BodyInfo): Flattened student records.

    Returns:
        Students: A list of parsed student records.
    """
    student_text = " ".join(body)
    tuid = r"((?:TU-)?(?<!\d)\d{5})"
    name = r"([^\d+]+)"
    rid = r"((?<!\d)\d{1,2})"
    student_pat = f"\\s*{rid}\\s+{tuid}\\s+{name}"

    students: Students = []
    last_lineno = 1

    for match in re.finditer(student_pat, student_text):
        lineno, tu_id, stud_name = match.groups()
        cur_lineno = is_number(lineno)

        if students and cur_lineno != last_lineno + 1:
            logger.warning(
                f"Line numbers out of order: expected {last_lineno + 1}, got {cur_lineno}"
            )

        last_lineno = cur_lineno
        students.append((lineno, tu_id, stud_name))
        logger.info(f"Student extracted: {tu_id} | {stud_name}")

    return students


def build_long_table(crs: CrsData) -> pd.DataFrame:
    """
    Converts extracted courses into a Pandas DataFrame.

    Args:
        crs (CrsData): List of (header, students) tuples.

    Returns:
        pd.DataFrame: A structured DataFrame representation.
    """
    rows = []

    for i, (header, students) in enumerate(crs):
        hdr_dict = header
        hdr_dict["crsno"] = i

        for student in students:
            if len(student) != 3:
                logger.warning(f"Malformed student entry: {student}")
                continue

            row = {
                **hdr_dict,
                "LineNo": student[0],
                "StudentID": student[1],
                "FullName": student[2],
            }
            rows.append(row)

    rs = pd.DataFrame(rows)

    # splitint the Day/Time in 2 based on space
    rs = pd.concat(
        [rs, rs["Day/Time"].str.extract("(?P<days>^[^ ]*) (?P<time>.*)")], axis=1
    ).drop(columns="Day/Time")

    # splitting Course in Course code and Couse no
    rs = pd.concat(
        [rs, rs["Course"].str.extract("(?P<course_code>^[^ ]*) (?P<course_no>.*)")],
        axis=1,
    )
    # add a course id != course no
    rs.loc[:, "crsid"] = (
        rs.Course.str.replace(" ", "_") + "-s" + rs.Section.apply(lambda x: f"{x:0>2}")
    )
    rs = rs.drop(columns="Course")

    rs = rs.rename(
        columns={
            "Course Title": "course_title",
            "Instructor": "instructor",
            "Section": "section",
            "LineNo": "lineno",
            "StudentID": "studid",
            "FullName": "fullname",
        }
    )

    return rs


def parse_header_keys(tokens: HeaderInfo) -> CrsHeader:
    """
    Extracts header key-value pairs from tokens.

    Args:
        tokens (HeaderInfo): List of header tokens.

    Returns:
        CrsHeader: Parsed key-value dictionary.
    """
    result = {}
    used_keys = set()

    for i in range(len(tokens)):
        key = tokens[i]
        if key in COURSE_HEADER_KEYS and key not in used_keys:
            used_keys.add(key)
            value = (
                tokens[i + 1]
                if i + 1 < len(tokens) and tokens[i + 1] not in COURSE_HEADER_KEYS
                else ""
            )
            # We want to do a special treatment for Day/Time key because some courses with only
            # one student get the values mixed up during convertion from the pdf
            # and the studnet line number '1' get inserted just before the Date time (when it existe)
            # in that case I want to remove the 1 and use the next value if it exist.
            # so the next line override value in that case
            if key == "Day/Time" and value == "1":
                if i + 2 == len(tokens):
                    # nothing after the 1, the date is the last token to take from the list
                    value = ""
                else:
                    value = tokens[i + 2]

            result[key] = value.strip(": ")

    return result


def is_number(value: str) -> Any:
    """
    Attempts to parse a number.

    Args:
        value (str): The string to convert.

    Returns:
        Any: Parsed number or None.
    """
    try:
        return int(value)
    except ValueError:
        return None
