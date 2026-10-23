# Student Grade Calculator

A dependency-free Python command-line app that calculates total marks, percentage,
overall grade, pass/fail status, and a subject-wise performance report.

## Features

- Interactive mark entry or JSON input
- Configurable maximum marks per subject
- Overall total, percentage, grade, and pass/fail status
- Subject-wise percentage, grade, performance remark, and status
- Best subject and focus areas (subjects below 60%)
- Text report or machine-readable JSON output
- Input validation and clear error messages

A student passes only when every subject scores at least 40%.

## Requirements

Python 3.10 or newer. No third-party packages are needed.

## Usage

Run from this directory:

```powershell
# Interactive mode
python main.py

# Use the included sample data
python main.py --input sample_student.json

# Try the built-in demo
python main.py --demo

# Print JSON instead of a text report
python main.py --input sample_student.json --json

# Save the report to a file
python main.py --demo --output report.txt
```

Options:

| Option | Description |
| --- | --- |
| `-i, --input FILE` | Read a student and subjects from JSON |
| `--demo` | Use sample student data |
| `--json` | Output JSON instead of a text report |
| `-o, --output FILE` | Save output to a file |

## JSON input format

```json
{
  "name": "Aarav Sharma",
  "subjects": [
    { "name": "Mathematics", "marks": 92, "max_marks": 100 },
    { "name": "Physics", "marks": 88, "max_marks": 100 },
    { "name": "Chemistry", "marks": 79 }
  ]
}
```

`max_marks` is optional and defaults to `100`. Marks must be between `0` and
`max_marks`, inclusive.

## Grading scale

| Percentage | Grade | Remark |
| --- | --- | --- |
| 90-100 | A+ | Outstanding |
| 80-89.99 | A | Excellent |
| 70-79.99 | B | Very Good |
| 60-69.99 | C | Good |
| 50-59.99 | D | Average |
| 40-49.99 | E | Needs Improvement |
| Below 40 | F | Fail |

## Sample report

```text
=================================================================
                       STUDENT GRADE REPORT
=================================================================
Student : Aarav Sharma
Result  : PASS
-----------------------------------------------------------------
Subject           Marks  Max  Score %  Grade  Status  Performance
-----------------------------------------------------------------
Mathematics       92     100  92.00%   A+     Pass    Outstanding
Physics           88     100  88.00%   A      Pass    Excellent
Chemistry         79     100  79.00%   B      Pass    Very Good
English           95     100  95.00%   A+     Pass    Outstanding
Computer Science  98     100  98.00%   A+     Pass    Outstanding
-----------------------------------------------------------------
Total Marks   : 452 / 500
Percentage    : 90.40%
Overall Grade : A+ (Outstanding)
Best Subject  : Computer Science (98.00%)
Focus Areas   : None
=================================================================
```

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Project structure

```text
student-grade-calculator/
├── grade_calculator.py   # Validation, calculations, grading, report formatting
├── main.py               # CLI and interactive prompts
├── sample_student.json   # Example input
├── tests/
│   └── test_grade_calculator.py
└── README.md
```
=======
# student-grade-calculator
>>>>>>> db577e7949d4e93455026776774af4ea060a65c6
