"""Core grade calculation logic for the Student Grade Calculator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

PASS_MARK = 40.0
DEFAULT_MAX_MARKS = 100.0


@dataclass(frozen=True)
class Grade:
    letter: str
    remark: str


GRADE_SCALE: tuple[tuple[float, Grade], ...] = (
    (90.0, Grade("A+", "Outstanding")),
    (80.0, Grade("A", "Excellent")),
    (70.0, Grade("B", "Very Good")),
    (60.0, Grade("C", "Good")),
    (50.0, Grade("D", "Average")),
    (40.0, Grade("E", "Needs Improvement")),
    (0.0, Grade("F", "Fail")),
)


def grade_for(percentage: float) -> Grade:
    """Return the grade for a percentage on the configured 0-100 scale."""
    if not 0.0 <= percentage <= 100.0:
        raise ValueError("Percentage must be between 0 and 100.")
    for minimum, grade in GRADE_SCALE:
        if percentage >= minimum:
            return grade
    return GRADE_SCALE[-1][1]


@dataclass(frozen=True)
class Subject:
    name: str
    marks: float
    max_marks: float = DEFAULT_MAX_MARKS

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Subject name cannot be empty.")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "marks", _to_number(self.marks, "Marks"))
        object.__setattr__(
            self, "max_marks", _to_number(self.max_marks, "Maximum marks")
        )
        if self.max_marks <= 0:
            raise ValueError(f"Maximum marks for '{self.name}' must be greater than 0.")
        if not 0 <= self.marks <= self.max_marks:
            raise ValueError(
                f"Marks for '{self.name}' must be between 0 and "
                f"{_format_number(self.max_marks)}."
            )

    @property
    def percentage(self) -> float:
        return self.marks / self.max_marks * 100.0

    @property
    def grade(self) -> Grade:
        return grade_for(self.percentage)

    @property
    def passed(self) -> bool:
        return self.percentage >= PASS_MARK

    @property
    def status(self) -> str:
        return "Pass" if self.passed else "Fail"


@dataclass(frozen=True)
class StudentResult:
    name: str
    subjects: tuple[Subject, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Student name cannot be empty.")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "subjects", tuple(self.subjects))

        if not self.subjects:
            raise ValueError("At least one subject is required.")
        if not all(isinstance(subject, Subject) for subject in self.subjects):
            raise TypeError("subjects must contain only Subject instances.")

    @property
    def total_marks(self) -> float:
        return sum(subject.marks for subject in self.subjects)

    @property
    def total_max_marks(self) -> float:
        return sum(subject.max_marks for subject in self.subjects)

    @property
    def percentage(self) -> float:
        return self.total_marks / self.total_max_marks * 100.0

    @property
    def grade(self) -> Grade:
        return grade_for(self.percentage)

    @property
    def passed(self) -> bool:
        return all(subject.passed for subject in self.subjects)

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"

    @property
    def best_subject(self) -> Subject:
        return max(self.subjects, key=lambda subject: subject.percentage)

    @property
    def focus_subjects(self) -> tuple[Subject, ...]:
        """Subjects scoring below 60%, ordered weakest first."""
        return tuple(
            sorted(
                (subject for subject in self.subjects if subject.percentage < 60.0),
                key=lambda subject: subject.percentage,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "subjects": [
                {
                    "name": subject.name,
                    "marks": subject.marks,
                    "max_marks": subject.max_marks,
                }
                for subject in self.subjects
            ],
            "total_marks": round(self.total_marks, 2),
            "total_max_marks": round(self.total_max_marks, 2),
            "percentage": round(self.percentage, 2),
            "grade": self.grade.letter,
            "status": self.status,
            "subject_performance": [
                {
                    "name": subject.name,
                    "marks": subject.marks,
                    "max_marks": subject.max_marks,
                    "percentage": round(subject.percentage, 2),
                    "grade": subject.grade.letter,
                    "performance": subject.grade.remark,
                    "status": subject.status,
                }
                for subject in self.subjects
            ],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> StudentResult:
        if not isinstance(data, Mapping):
            raise ValueError("Student data must be a JSON object.")
        if "name" not in data:
            raise ValueError("Student data is missing the 'name' field.")
        if "subjects" not in data:
            raise ValueError("Student data is missing the 'subjects' field.")

        raw_subjects = data["subjects"]
        if not isinstance(raw_subjects, list) or not raw_subjects:
            raise ValueError("'subjects' must be a non-empty list.")

        subjects = []
        for index, raw_subject in enumerate(raw_subjects, start=1):
            if not isinstance(raw_subject, Mapping):
                raise ValueError(f"Subject {index} must be a JSON object.")
            missing = {"name", "marks"} - raw_subject.keys()
            if missing:
                fields = ", ".join(sorted(missing))
                raise ValueError(f"Subject {index} is missing: {fields}.")
            subjects.append(
                Subject(
                    name=raw_subject["name"],
                    marks=raw_subject["marks"],
                    max_marks=raw_subject.get("max_marks", DEFAULT_MAX_MARKS),
                )
            )

        return cls(name=data["name"], subjects=tuple(subjects))


def format_report(result: StudentResult) -> str:
    """Render a plain-text report with overall and subject-wise results."""
    headers = ("Subject", "Marks", "Max", "Score %", "Grade", "Status", "Performance")
    rows = [
        (
            subject.name,
            _format_number(subject.marks),
            _format_number(subject.max_marks),
            f"{subject.percentage:.2f}%",
            subject.grade.letter,
            subject.status,
            subject.grade.remark,
        )
        for subject in result.subjects
    ]

    widths = [
        max(len(headers[column]), *(len(row[column]) for row in rows))
        for column in range(len(headers))
    ]

    def render_row(row: Iterable[str]) -> str:
        cells = [str(value).ljust(widths[index]) for index, value in enumerate(row)]
        return "  ".join(cells).rstrip()

    divider = "-" * (sum(widths) + 2 * (len(widths) - 1))
    lines = [
        "=" * len(divider),
        "STUDENT GRADE REPORT".center(len(divider)),
        "=" * len(divider),
        f"Student : {result.name}",
        f"Result  : {result.status}",
        divider,
        render_row(headers),
        divider,
        *(render_row(row) for row in rows),
        divider,
        f"Total Marks   : {_format_number(result.total_marks)} / "
        f"{_format_number(result.total_max_marks)}",
        f"Percentage    : {result.percentage:.2f}%",
        f"Overall Grade : {result.grade.letter} ({result.grade.remark})",
        f"Best Subject  : {result.best_subject.name} "
        f"({result.best_subject.percentage:.2f}%)",
    ]

    if result.focus_subjects:
        focus = ", ".join(
            f"{subject.name} ({subject.percentage:.2f}%)"
            for subject in result.focus_subjects
        )
        lines.append(f"Focus Areas   : {focus}")
    else:
        lines.append("Focus Areas   : None")

    lines.append("=" * len(divider))
    return "\n".join(lines)


def _to_number(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number.")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} must be a number.") from error
    if number != number or number in (float("inf"), float("-inf")):
        raise ValueError(f"{label} must be a finite number.")
    return number


def _format_number(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")
