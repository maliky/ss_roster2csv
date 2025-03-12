"""
helper.py
Regroupe utility function to help investigate and debug the program
"""


def get_course_by_code(course_code, courses):
    return [(i, c) for i, c in enumerate(courses) if course_code in c][0]


def get_crdata_by_code(course_code, crdata):
    return [(i, c) for i, c in enumerate(crdata) if course_code in c[0].values()][0]


def get_course_with_lt(effectif, crdata):
    return [
        (i, len(c[1]), c[0]["Course"])
        for i, c in enumerate(crdata)
        if len(c[1]) < effectif
    ]

def get_course_with_exactly(effectif, crdata):
    return [
        (i, len(c[1]), c[0]["Course"])
        for i, c in enumerate(crdata)
        if len(c[1]) ==  effectif
    ]
