from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from grade_calculator import (  # noqa: E402
    StudentResult,
    Subject,
    format_report,
    grade_for,
)
from main import main  # noqa: E402


class GradeTests(unittest.TestCase):
    def test_grade_boundaries(self) -> None:
        cases = {
            100: "A+",
            90: "A+",
            89.99: "A",
            80: "A",
            79.99: "B",
            70: "B",
            60: "C",
            50: "D",
            40: "E",
            39.99: "F",
            0: "F",
        }
        for percentage, expected in cases.items():
            with self.subTest(percentage=percentage):
                self.assertEqual(grade_for(percentage).letter, expected)

    def test_percentage_outside_range_is_rejected(self) -> None:
        for percentage in (-0.1, 100.1):
            with self.subTest(percentage=percentage):
                with self.assertRaises(ValueError):
                    grade_for(percentage)


class SubjectTests(unittest.TestCase):
    def test_percentage_grade_and_status(self) -> None:
        subject = Subject("Mathematics", 85, 100)
        self.assertEqual(subject.percentage, 85)
        self.assertEqual(subject.grade.letter, "A")
        self.assertEqual(subject.grade.remark, "Excellent")
        self.assertTrue(subject.passed)
        self.assertEqual(subject.status, "Pass")

    def test_subject_name_is_trimmed(self) -> None:
        subject = Subject("  Physics  ", 70)
        self.assertEqual(subject.name, "Physics")
        self.assertEqual(subject.max_marks, 100)

    def test_invalid_subjects_are_rejected(self) -> None:
        invalid_subjects = (
            ("", 50, 100),
            ("Math", -1, 100),
            ("Math", 101, 100),
            ("Math", 50, 0),
            ("Math", float("nan"), 100),
            ("Math", True, 100),
        )
        for name, marks, maximum in invalid_subjects:
            with self.subTest(name=name, marks=marks, maximum=maximum):
                with self.assertRaises(ValueError):
                    Subject(name, marks, maximum)


class StudentResultTests(unittest.TestCase):
    def test_totals_and_percentage(self) -> None:
        result = StudentResult(
            "Riya",
            (
                Subject("Mathematics", 80, 100),
                Subject("Science", 45, 50),
            ),
        )
        self.assertEqual(result.total_marks, 125)
        self.assertEqual(result.total_max_marks, 150)
        self.assertAlmostEqual(result.percentage, 83.3333, places=4)
        self.assertEqual(result.grade.letter, "A")
        self.assertEqual(result.status, "PASS")

    def test_failed_subject_fails_the_overall_result(self) -> None:
        result = StudentResult(
            "Kabir",
            (
                Subject("Mathematics", 95),
                Subject("Physics", 35),
            ),
        )
        self.assertAlmostEqual(result.percentage, 65)
        self.assertEqual(result.grade.letter, "C")
        self.assertFalse(result.passed)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.subjects[1].status, "Fail")

    def test_best_and_focus_subjects(self) -> None:
        result = StudentResult(
            "Meera",
            (
                Subject("Mathematics", 55),
                Subject("Physics", 30),
                Subject("English", 90),
            ),
        )
        self.assertEqual(result.best_subject.name, "English")
        self.assertEqual(
            [subject.name for subject in result.focus_subjects],
            ["Physics", "Mathematics"],
        )

    def test_empty_student_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            StudentResult("", (Subject("Math", 50),))
        with self.assertRaises(ValueError):
            StudentResult("Riya", ())

    def test_json_round_trip(self) -> None:
        original = StudentResult(
            "Aarav",
            (Subject("Mathematics", 92, 100), Subject("Art", 45, 50)),
        )
        restored = StudentResult.from_dict(original.to_dict())

        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.total_marks, original.total_marks)
        self.assertEqual(restored.grade.letter, original.grade.letter)
        self.assertEqual(restored.status, original.status)
        self.assertEqual(
            [(subject.name, subject.marks) for subject in restored.subjects],
            [("Mathematics", 92), ("Art", 45)],
        )

    def test_report_contains_overall_and_subject_results(self) -> None:
        result = StudentResult(
            "Aarav",
            (Subject("Mathematics", 92), Subject("Physics", 55)),
        )
        report = format_report(result)

        self.assertIn("STUDENT GRADE REPORT", report)
        self.assertIn("Aarav", report)
        self.assertIn("Mathematics", report)
        self.assertIn("92", report)
        self.assertIn("A+", report)
        self.assertIn("Focus Areas", report)
        self.assertIn("Physics (55.00%)", report)


class CommandLineTests(unittest.TestCase):
    def run_cli(self, args: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(args)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_demo_text_report(self) -> None:
        code, stdout, _ = self.run_cli(["--demo"])
        self.assertEqual(code, 0)
        self.assertIn("Aarav Sharma", stdout)
        self.assertIn("Overall Grade : A+", stdout)

    def test_input_json_and_json_output(self) -> None:
        data = {
            "name": "Nisha",
            "subjects": [
                {"name": "Math", "marks": 76},
                {"name": "Science", "marks": 88, "max_marks": 100},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "student.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            code, stdout, _ = self.run_cli(["--input", str(path), "--json"])

        self.assertEqual(code, 0)
        output = json.loads(stdout)
        self.assertEqual(output["name"], "Nisha")
        self.assertEqual(output["percentage"], 82.0)
        self.assertEqual(output["grade"], "A")
        self.assertEqual(len(output["subject_performance"]), 2)

    def test_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.txt"
            code, stdout, _ = self.run_cli(["--demo", "--output", str(path)])
            content = path.read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn("Report saved", stdout)
        self.assertIn("STUDENT GRADE REPORT", content)

    def test_invalid_json_returns_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text("{not json", encoding="utf-8")
            code, _, stderr = self.run_cli(["--input", str(path)])

        self.assertEqual(code, 1)
        self.assertIn("Invalid JSON", stderr)

    def test_interactive_flow(self) -> None:
        answers = iter(
            ["Riya", "2", "Mathematics", "100", "80", "Science", "50", "45"]
        )
        stdout = io.StringIO()
        with (
            patch("builtins.input", side_effect=lambda _: next(answers)),
            redirect_stdout(stdout),
        ):
            code = main([])

        self.assertEqual(code, 0)
        self.assertIn("Riya", stdout.getvalue())
        self.assertIn("83.33%", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
