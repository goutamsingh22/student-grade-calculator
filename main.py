"""Command-line interface for the Student Grade Calculator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from grade_calculator import (
    DEFAULT_MAX_MARKS,
    StudentResult,
    Subject,
    format_report,
)

DEMO_RESULT = StudentResult(
    name="Aarav Sharma",
    subjects=(
        Subject("Mathematics", 92),
        Subject("Physics", 88),
        Subject("Chemistry", 79),
        Subject("English", 95),
        Subject("Computer Science", 98),
    ),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calculate totals, percentages, grades, and subject performance."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "-i",
        "--input",
        type=Path,
        metavar="FILE",
        help="read student marks from a JSON file",
    )
    source.add_argument(
        "--demo",
        action="store_true",
        help="run with sample student data",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the result as JSON instead of a text report",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="FILE",
        help="save the report to a file",
    )
    return parser


def load_result(path: Path) -> StudentResult:
    if not path.is_file():
        raise ValueError(f"Input file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Invalid JSON in {path} at line {error.lineno}, column {error.colno}."
        ) from error
    return StudentResult.from_dict(data)


def interactive_result() -> StudentResult:
    print("\nStudent Grade Calculator")
    print("Enter marks for each subject. Press Ctrl+C to exit.\n")

    name = _prompt_text("Student name: ")
    subject_count = _prompt_int("Number of subjects: ", minimum=1)

    subjects = []
    for index in range(1, subject_count + 1):
        print(f"\nSubject {index}")
        subject_name = _prompt_text("  Name: ")
        max_marks = _prompt_float(
            f"  Maximum marks [{DEFAULT_MAX_MARKS:g}]: ",
            default=DEFAULT_MAX_MARKS,
            minimum_exclusive=0,
        )
        marks = _prompt_float(
            "  Marks obtained: ",
            minimum=0,
            maximum=max_marks,
        )
        subjects.append(Subject(subject_name, marks, max_marks))

    return StudentResult(name=name, subjects=tuple(subjects))


def _prompt_text(label: str) -> str:
    while True:
        value = input(label).strip()
        if value:
            return value
        print("  Value cannot be empty.")


def _prompt_int(label: str, minimum: int) -> int:
    while True:
        raw = input(label).strip()
        try:
            value = int(raw)
        except ValueError:
            print(f"  Enter a whole number of at least {minimum}.")
            continue
        if value < minimum:
            print(f"  Enter a whole number of at least {minimum}.")
            continue
        return value


def _prompt_float(
    label: str,
    *,
    default: float | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
    minimum_exclusive: float | None = None,
) -> float:
    while True:
        raw = input(label).strip()
        if not raw and default is not None:
            return default

        try:
            value = float(raw)
        except ValueError:
            print("  Enter a valid number.")
            continue

        if value != value or value in (float("inf"), float("-inf")):
            print("  Enter a finite number.")
            continue
        if minimum is not None and value < minimum:
            print(f"  Value must be at least {minimum:g}.")
            continue
        if minimum_exclusive is not None and value <= minimum_exclusive:
            print(f"  Value must be greater than {minimum_exclusive:g}.")
            continue
        if maximum is not None and value > maximum:
            print(f"  Value cannot exceed {maximum:g}.")
            continue
        return value


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.input is not None:
            result = load_result(args.input)
        elif args.demo:
            result = DEMO_RESULT
        else:
            result = interactive_result()

        if args.json:
            output = json.dumps(result.to_dict(), indent=2)
        else:
            output = format_report(result)
    except (ValueError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 130

    if args.output is not None:
        try:
            args.output.write_text(output + "\n", encoding="utf-8")
        except OSError as error:
            print(f"Error: could not write {args.output}: {error}", file=sys.stderr)
            return 1
        print(f"Report saved to {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
