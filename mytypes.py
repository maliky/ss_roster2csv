from typing import Tuple, TypeAlias, TypedDict, Literal, List


class CrsHeader(TypedDict, total=False):
    Course: str
    Semester: Literal["1", "2"]
    Course_Title: str
    Instructor: str
    Section: str
    DayTime: str


Student: TypeAlias = Tuple[None | str, str, str]
Students: TypeAlias = List[Student]
Page: TypeAlias = List[str]
Pages: TypeAlias = List[Page]
Course: TypeAlias = List[str]
Courses: TypeAlias = List[Course]
StudentData: TypeAlias = Tuple[str, str, str]
CrsData: TypeAlias = Tuple[List[str], List[StudentData]]
HeaderInfo: TypeAlias = List[str]
BodyInfo: TypeAlias = List[str]
CourseInfo: TypeAlias = Tuple[HeaderInfo, Students]
CoursesInfo: TypeAlias = List[CourseInfo]
