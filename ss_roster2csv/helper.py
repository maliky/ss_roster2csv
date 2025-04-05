"""
helper.py
Regroupe utility function to help investigate and debug the program
"""

### using df
import pandas as pd


def crs_of_inst(df, name):
    """
    return the courses taught by the instructor name
    """
    instructor_courses = df.groupby("instructor")
    return df.loc[
        instructor_courses.groups[name], ["crsid", "course_title"]
    ].drop_duplicates()


def chunk(seq, n):
    """Split seq into chunks of size n."""
    return [seq[i : i + n] for i in range(0, len(seq), n)]


def pf_line(chunk, width=30):
    """Format a single row into columns with '.' padding, but not for the last column."""
    formatted = list(
        map(lambda c: f"{c:.<{width}}", chunk[:-1])
    )  # Apply format to all but the last
    formatted.append(chunk[-1])  # Append last element without dots
    return " ".join(formatted)


def pf_in_columns(seq, cols=3, width=30):
    """Format seq into columns, aligning with '.' and width."""
    chunks = chunk(seq, cols)
    return "\n".join(map(pf_line, chunks))


def show_crs_by_number(courses_stud, text):
    crs = list(courses_stud.values)
    print(f"We have {len(courses_stud)} courses with {text}:\n")
    for c, t, i, students in crs:
        print(f"{c} '{t}' {i}:")
        for stud in sorted(students, key=lambda x: x[1]):
            print(f"  {stud[1]:.<35} {stud[0]}")
        print("")


def get_courses_by_student_count(df: pd.DataFrame, student_count: int = 1):
    """
    Retrieve courses with exactly a given number of students.

    Args:
        df (pd.DataFrame): The roster dataframe containing course and student data.
        student_count (int): The exact number of students a course should have.

    Returns:
        pd.DataFrame: A dataframe with crsid, course_title, and a list of (studid, fullname).
    """
    # Count students per course
    crs_cnt = df.groupby("crsid")["studid"].count()

    # Get courses with exactly the specified student count
    filtered_crs = crs_cnt[crs_cnt == student_count].index

    # Filter original DataFrame and group by crsid, course_title
    result = (
        df[df["crsid"].isin(filtered_crs)][
            ["crsid", "course_title", "instructor", "studid", "fullname"]
        ]
        .groupby(["crsid", "course_title", "instructor"], group_keys=False)
        .apply(lambda g: list(zip(g["studid"], g["fullname"])))
        .reset_index(name="students")
    )

    return result


### using crdata and courses but broken
def flatten(nested_list):
    return [item for sublist in nested_list for item in sublist]


def get_all_students(crd):
    return flatten([c[1] for c in crd])


def get_instructors_courses(crdata):
    "return the list of all instrutors and the number of courses"
    inst = get_instructors(crdata)
    ret = [(i, get_instructor_course_nb(i, crdata)) for i in inst]
    return sorted(ret, key=lambda x: x[1], reverse=True)


def get_instructor_course_nb(name, crdata):
    "return the number of course of an instructor"
    return len(get_instructor_courses(name, crdata))


def get_number_student_in_course(course_code, crdata):
    "return the number of student for  an instructor and a course"
    students = get_stud_from_course(course_code, crdata)
    return len(students)


def get_instructors(df):
    return df[~df["instructor"].isin(["", "Staff"])]


def get_instructors_crdata(crdata):
    instructors = set(map(lambda c: c[0]["Instructor"], crdata))
    instructors -= {"", "Staff"}
    return sorted(list(instructors))


def get_course_by_code(course_code, courses):
    return [(i, c) for i, c in enumerate(courses) if course_code in c][0]


def get_crdata_by_code(course_code, crdata):
    return [(i, c) for i, c in enumerate(crdata) if course_code in c[0]["Course"]()][0]


def get_instructor_courses(name, crdata):
    """
    Get the all the courses code for the instructor name
    """
    courses = []
    for c in crdata:
        if c[0]["Instructor"] == name:
            course = (c[0]["Course"] + " s" + c[0]["Section"], c[0]["Course Title"])
            courses.append(course)
    return courses


def get_course_with_lt(effectif, crdata):
    return [
        (i, c[0]["Course"], c[0]["Course Title"])
        for i, c in enumerate(crdata)
        if len(c[1]) < effectif
    ]


def get_course_with_exactly(effectif, crdata, with_students=True):
    crs = []
    for i, c in enumerate(crdata):
        cond = len(c[1]) == effectif
        if cond:
            if with_students:
                course = c[0]["Course"], c[0]["Course Title"], [s[1:] for s in c[1]]
            else:
                course = c[0]["Course"], c[0]["Course Title"], effectif

            crs.append(course)
    return crs


def get_stud_from_course(course_code, crdata):
    course = get_course_by_code(course_code, crdata)
    return course[2]


def get_stud_from_courses(crdata):
    """Get the list of students from a list of courses"""
    slist = []
    for c in crdata:
        students = get_student_from_course(c, crdata)
        if len(studs):
            slist = slist + students
        else:
            slist = students
    return set(slist)
